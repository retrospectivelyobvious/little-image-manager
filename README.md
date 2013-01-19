# Little Image Manager
The Little Image Manager (LIM) is a package management system for OS images.
It's intended for use with embedded Linux systems such as the Raspberry Pi,
BeagleBoard, Pandaboard, etc. It allows you to easily save, archive, manage,
and restore the disk images used on these devices. LIM has the advantage of a
more targeted compression strategy than the typical dd/gzip combination used
for storing such images. Due to this strategy LIM is able to produce images
which can be significantly smaller than those produced by dd/gzip for many
systems. (I've observed LIM images that are half the size of their dd/gzip
equivalents, see 'How LIM Works' below for more detail.) Additionally, LIM can
store meta-information about an image within its container format which can be
useful for constructing image repositories and the like.

LIM's goal is to enable easier experimentation in building new OS images,
porting OSes, writing custom kernels, and performing OS development, etc,
without the requirement of managing dozens of SD cards.  LIM is intended to
work with the microSD cards that often serve as the primary storage in embedded
systems, but should work with anything that can present itself as a block
device in a Linux system.

## Installation
To get started with LIM, first grab the source:

    git clone git://github.com/retrospectivelyobvious/little-image-manager.git
    cd little-image-manager

LIM makes use of a few common Linux utilities to get its job done, be sure
you've satisfied the dependencies:

    sudo apt-get install gzip coreutils binutils parted python-parted

Then install LIM by running setup.py:

    sudo ./setup.py install

## Basic Usage
LIM's fundamental operation is to store and restore system images. To do this
it requires you to communicate both source and destination for the operation.
This is done through switches passed to the program.  Generally speaking the
letter used in the switch indicates what type of media is to be read
from/written to, while the case of that switch indicates whether that option
is communicating the source or destination. For example '-d /dev/sdX' indicates
a device being used as the source for an operation while '-A somefile'
indicates an archive file being used as a destination.

(NB: Unless you've been diligent about setting your device privileges, you'll
probably need to be root to execute many of these commands. Treat LIM with the
same respect you'd give dd/parted/fdisk/etc - it will ruin your day if you
target the wrong device.)

Copy a disk image from an SD card to an archive:

    lim -d /dev/sdX -A somefile.lim

Copy a disk image from an SD card to an archive (don't prompt for meta-info):

    lim -M -d /dev/sdX -A somefile.lim

Copy a disk image from an SD card to an archive (use bzip2 compression):

    lim -z bzip -M -d /dev/sdX -A somefile.lim

Restore a disk image from an archive to an SD card:

    lim -a somefile.lim -D /dev/sdX

Restore a disk image from a url to an SD card:

    lim -u someurl.lim -D /dev/sdX

When creating an archive, LIM will prompt you for some descriptive meta data
about the disk image. Providing the information is optional, but it is useful
for organizational purposes or if your image finds its way into a repository.
To see a description of the types of meta data and suggested
formats/conventions when providing them, see the section "The 'meta' file" at
the end of this document.

## Advanced Usage
### Manipulate Partition Sizes
When restoring an image, LIM can attempt to resize the image's partitions to
fit the destination disk if the destination's size differs from that of the
source image. It can both expand partitions and shrink them. Shrinking is
obviously limited by the relative sizes of the data and the requested partition
size (sorry, no magic here). You can also change the file system type when
restoring the image.

Specifying a partition size/type is done with the following switch:

    -pN:start:len:fstype

* N - the partition number to alter
* start - the location you want the partition to begin (in sectors, from
        start of disk)
* len - the size of the partition (in sectors)
* fstype - the file system type (ext2,ext3,ext4,fat16,fat32)

You can use the programs 'parted' or 'fdisk' to get information about the
number of available sectors.

To get information about the geometry of the image's source disk, you can print
out the meta file by using the command 'ar p somefile.lim meta' from the shell.

Example:  
(a 1GB partition, starting at sector 2048, of type ext2)

    lim -a somefile.lim -D /dev/sdX -p1:2048:2097152:ext2


*CAUTION:*  
Be aware that if you change a partition's end boundary you will need to adjust
the location of each subsequent partition's start so as not to create an
overlap. Also be aware that changing partition types may interfere with the
operation of certain boot loaders.

### Force Block Storage (Make LIM use dd)
When creating archives from a physical disk, LIM's default behavior is to
tarball and compress the contents of each partition while storing the metadata
(partition size, filesystem type, etc) that will eventually be needed to
reconstruct it. Generally this results in much better compression performance,
but occasionally it doesn't work (e.g. if you're using a file system LIM
doesn't understand, doing raw writes to the disk for whatever reason, etc). In
these circumstances, you can tell LIM to store a particular partition as a data
block (i.e. use 'dd' to store that partition's data).

    lim -PN:block

where 'N' is the partition number

Make an archive named 'somefile.lim' out of sdd, where partition 1 is
stored using 'dd' and other partitions are stored as tarballs:

    lim -d /dev/sdd -P1:block -A somefile.lim

### Specify Compression Type
By default, LIM uses gzip to compress the tarballs or block files that contain
the partition data. If desired, you can tell LIM to use a different compression
program. (bzip, xz, gzip)

Specify alternation compression program:

    lim -z bzip -d /dev/sdX -A somefile.lim

## How LIM Works

LIM takes its inspiration mostly from the Debian package management tools and
their 'deb' format. LIM archives are simple 'ar' archives that contain a
series of compressed partition images and a meta info file that describes each
of those partitions (sizes of partitions, types of file systems, the MBR, etc).
Each of the partitions can be stored either as a compressed tarball of the file
system contents (default) or as a compressed block file read by 'dd'. The MBR
and the interstitial space between the end of the MBR and the start of the
first partition (which is sometimes used for bootloader code) are stored
as compressed blocks.

Currently, LIM only supports devices with old-style DOS partition tables
(pretty much all embedded systems use these), and only supports primary
partitions (sorry, no logical or extended partition support yet - soon).

The reason that LIM can often outperform dd/gzip, and the reason that the gains
are sometimes much better than others, is that LIM is storing only the files on
the device as opposed to a full system image. When a full system image is
stored (as with dd), all of the information between files as well as all of the
'dead-files' are picked up in the read. (Remember, most file systems don't zero
out deleted files, they only delete the associated bookkeeping information.)
This means that the more heavily used the file system was before the read, the
more entropy exists in the dead space of the file system, and the more will be
picked up by dd. This bloats the _compressed_ image needlessly, as gzip will
preserve the worthless information.

### The 'meta' File

The following fields are user specified during image creation:

* name - A short name for the image. This should be one word (no spaces), be all
       lower case, and contain only alpha-numeric characters (no symbols)

* description - Up to a paragraph of descriptive text explaining what the image is

* url - A reference url where one can go for more information on the image, an
      author's homepage, etc. (This should not be the exact URL the image was
      retrieved from.)

* img_ver - A version number for the image itself. This is chosen at the author's
          discretion.

The remaining fields in the meta file are not user specified, they are based on
the version of LIM used to create the image, and the settings given to it
during creation:

* format_ver - The LIM archive format that the image matches. This is assigned by
             LIM when it creates the archive. It is used to ensure that
             different versions of LIM can deal appropriately with the
             archive's feature set.

* compression - The compression program used to store the partition
              tarball/blocks.

You can view the meta file for an archive using the 'ar' utility:

    ar p archive.lim meta
