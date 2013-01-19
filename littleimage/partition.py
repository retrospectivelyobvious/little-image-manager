#Little Image Manager
#Copyright (C) 2012 Robert (Bob) M. Sherbert
#
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#If by some strange twist you believe that this software would have value for a
#commercial project but are unwilling to be bound by the strictures of the GPL,
#you may contact the author with inquiries for alternative licence terms.

import os, sys
import subprocess

import errors
import support

class Partition(object):
    def __init__(self, number, start, size, fstype, msdoslabel, parttype=None,\
                 device=None, flags={}, storage='tarball'):
        self.number = int(number) #the partition number /dev/sda1 = 1
        self.start = int(start) #location at which the partition starts (in sectors)
        self.size = int(size) #length of the partition (in sectors)
        self.fstype = str(fstype)
        self.parttype = parttype  #'primary' or 'extended', None -> no override
        self.device = device    #the path to the parted block device '/dev/sda'
        self.flags = flags
        self.msdoslabel = msdoslabel #msdos disk label, not used frequently but
                                     #uboot thinks its important
        self.storage = storage #'block' or 'tarball', indicates storage type

    @property
    def end(self):
        return self.start + self.size - 1

    @property
    #sector number at which the partition starts
    def startSec(self):
        return self.start

    @property
    def node(self):
        return self.device + str(self.number)

    def get(self, compress):
        if self.storage == 'block':
            return self.getBlock(compress)
        elif self.storage == 'tarball':
            return self.getTarball(compress)

    def composeNode(self, root):
        return root + str(self.number)

    def buildConfig(self):
        flags = ''
        try:
            if(self.flags['boot']):
                flags += 'boot:'
        except KeyError:
            pass
        try:
            if(self.flags['lba']):
                flags += 'lba:'
        except KeyError:
            pass
        try:
            if(self.flags['lvm']):
                flags += 'lvm:'
        except KeyError:
            pass
            
        config = {'start':self.startSec, 'size':self.size, \
                  'type':self.parttype,  'filesystem':self.fstype, \
                  'label':self.msdoslabel, \
                  'storage':self.storage, 'flags':flags }
        return config

    def __str__(self):
        s = "Partition " + str(self.number) + ": [" + str(self.start) + ", " \
            + str(self.start + self.size) + "]s" + " " + self.fstype
        return s

class PartitionOptions(object):
    # destinataion partition options
    # -PN:block, -PN:tarball
    def __init__(self, args):
        self.storage = 'tarball'

        a = args.split(':')
        self.number = int(a[0])
        opt = a[1]
        if opt == 'block':
            self.storage = 'block'
        elif opt == 'tarball':
            self.storage = 'tarball'

class PartitionSpec(Partition):
    """
    Source Partition Option Parser
    format:    -pN:start:len:units:fstype

    N - partition number
    start - start of the partition
    len - size of the partition
    units - units that start & end are specified in
    fstype - file system type

    * start, end, units, and fstype should be in notation understood by the
      'parted' program
    """
    def __init__(self, args):
        a = args.split(':')
        units = a[3]
        #TODO: eventually we'll process units from something user specified
        #into sectors. For the moment, reject anything that's not already in
        #sectors
        if units != 's':
            raise UnitsError(units)

        super(PartitionSpec, self).__init__(\
            number = a[0], \
            start = int(a[1]), \
            size = int(a[2]), \
            fstype = a[4])

class PartExchangeDescriptor(object):
    """
    A description of a partition as rendered to a tempdir for exchange between
    two endpoints (block device, archive, etc)
    """
    def __init__(self, number, config, exchangeloc):
        self.number = number
        self.config = config
        self.exchangeloc = exchangeloc

class DiskPartition(Partition):
    def __init__(self, number, device, startSec, size, exchangeDir, \
                 parttype, fs, msdoslabel, flags, storage='tarball'):
        super(DiskPartition, self).__init__(\
            number = number, \
            start = startSec, \
            size = size, \
            fstype = fs, \
            msdoslabel = msdoslabel, \
            parttype = parttype, \
            device = device, \
            flags = flags, \
            storage = storage)
        self.exchangeDir = exchangeDir

    def getBlock(self, compress):
        self.exchangeFile = os.path.join(self.exchangeDir, \
                                         "p" + str(self.number))
        p = support.ddPopen(count=self.size, skip=self.startSec, \
                            infile=self.device, \
                            outfile=subprocess.PIPE)
        efd = open(self.exchangeFile, 'w+b')
        subprocess.call(compress.getCompressOpts(), stdin=p.stdout, stdout=efd)
        efd.close()

        return PartExchangeDescriptor(self.number, self.buildConfig(),
                                      self.exchangeFile)

    def getTarball(self, compress):
        self.exchangeFile = os.path.join(self.exchangeDir, \
                                         "p" + str(self.number))

        self.mountDir = os.path.join(self.exchangeDir, \
                                     "mount" + str(self.number))
        os.mkdir(self.mountDir)
        support.mount(device=self.device + str(self.number), dest=self.mountDir)

        efd = open(self.exchangeFile, 'w+b')
        tarp = support.tarCreate_Process(srcdir=self.mountDir)
        p = subprocess.call(compress.getCompressOpts(), stdin=tarp.stdout,
                            stdout=efd)
        efd.close()

        #support.tar(tarfile=self.exchangeFile, target='.', options='czf', \
        #            cwd=self.mountDir)
        support.umount(self.mountDir)

        return PartExchangeDescriptor(self.number, self.buildConfig(), self.exchangeFile)

class ArchivePartition(Partition):
    def __init__(self, number, archive, startSec, size, exchangeDir, parttype,\
                 fs, msdoslabel, flags, storage):
        super(ArchivePartition, self).__init__(\
            number=number, \
            start=startSec, \
            size=size, \
            parttype=parttype, \
            fstype=fs, \
            msdoslabel=msdoslabel, \
            flags=flags, \
            storage=storage)

        self.exchangeDir = exchangeDir
        self.ar = archive

    def getBlock(self, compress):
        self.exchangeFile = os.path.join(self.exchangeDir, \
                                         "p" + str(self.number))
        fd = support.arStream(self.ar, 'p' + str(self.number))
        efd = open(self.exchangeFile, 'w+b')
        subprocess.call(compress.getDecompressOpts(), stdin=fd, stdout=efd)
        efd.close()

        return PartExchangeDescriptor(self.number, self.buildConfig(), self.exchangeFile)

    def getTarball(self, compress):
        self.exchangeFile = support.arGet(self.ar, "p" + str(self.number), \
                                          self.exchangeDir)

        return PartExchangeDescriptor(self.number, self.buildConfig(), self.exchangeFile)

def adjustPartitions(limpartlist, partspecs, partopts):
    #TODO - need some significant sanity checking here
    for p in limpartlist:
        merge = False
        for s in partspecs:
            if s.number == p.number:
                p.start = s.start
                p.fstype = s.fstype
                if s.size < p.size:
                    sys.stderr.write("User specifed size for partition " \
                                     + str(p.number) \
                                     + " is less than original image size.\n")
                    sys.stderr.write("Please ensure that the total content "\
                                     + "size is less than the specified "\
                                     + "size.\n")
                p.size = s.size   
                merge = True
        for s in partopts:
            if s.number == p.number:
                p.storage = s.storage
    return limpartlist
