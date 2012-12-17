#!/usr/bin/env python

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

import getopt

import container
import repo
import partition as part
import hardware as hw

def convertImage(fromLoc, toLoc, partSpecs, partOpts):
    meta = fromLoc.getMeta()
    try:
        if float(meta['format_ver']) != float(hw.LIM_VERSION):
            print "The source (" + str(meta['format_ver']) + ") " \
                  + "was not created with this version of LIM (" + \
                  str(hw.LIM_VERSION) + ")."
            print "It is probably not safe to continue - bailing."
            return 3
    except:
        return 3

    toLoc.putMeta(meta)
    toLoc.putDisk(fromLoc.getDisk())

    lparts = fromLoc.getLimPartitions()
    lparts = part.adjustPartitions(lparts, partSpecs, partOpts)
    toLoc.putGeom(lparts)
    toLoc.putMBR(fromLoc.getMBR(), codeonly=True)
    for par in lparts:
        exchangeDesc = par.get()
        toLoc.putPartition(exchangeDesc)

    toLoc.finalize()

def usage():
    print( \
"""
Little Image Manager (LIM)
Usage:
\t-d, -a <file> : Specify source device (-d) or source archive (-a)
\t-u <URL> : Specify a source URL at which an archive is located
\t-r <URL> : Specify a source URL at which a repository manifest is located
\t-D, -A <file> : Specify destination device (-D) or destination archive (-A)
Partition Specification:
\tSource Options (respecify criteria from source)
\t-pN:start:len:units:fstype
\t\t N - partition number
\t\t start - starting point of partition (in units)
\t\t len - length of partition (in units)
\t\t units - the units to interpret start/len in (as recognized by parted, default sectors)
\t\t fstype - file system type to use for this partition (ext2,ext3,ext4,fat16,fat32)
\tDestination (specify storage container options:
\t\t-PN:block -- store partition #N as block data (dd)
\t\t-PN:tarball -- store partition #N as compressed filesystem
""")

def main(argv):
    try:
        opts, leftover = getopt.getopt(argv[1: ], 'd:a:u:r:D:A:p:P:',
                                                          ['src-device=',
                                                           'src-archive=',
                                                           'src-url=',
                                                           'src-repo=',
                                                           'dst-device=',
                                                           'dst-archive=',
                                                           'config='])
    except getopt.GetoptError:
        print "Invalid Options: "
        print "Usage!!"
        return 1

    src = None
    dst = None
    pspecs = []
    pops = []
    for opt,arg in opts:
        if   opt in ('-d', '--src-device'):
            if(src):
                raise Exception("May not have more than one source.")
            src = container.BlockDevice(arg, src=True)
        elif opt in ('-D', '--dst-device'):
            if(dst):
                raise Exception("May not have more than one destination.")
            dst = container.BlockDevice(arg)
        elif opt in ('-a', '--src-archive'):
            if(src):
                raise Exception("May not have more than one source.")
            src = container.Archive(arg, src=True)
        elif opt in ('-u', '--src-url'):
            if(src):
                raise Exception("May not have more than one source.")
            src = repo.URL(arg)
        elif opt in ('-r', '--src-repo'):
            if(src):
                raise Exception("May not have more than one source.")
            src = repo.Repo(arg)
        elif opt in ('-A', '--dst-archive'):
            if(dst):
                raise Exception("May not have more than one destination.")
            dst = container.Archive(arg)
        elif opt in ('-p'):
            pspecs.append(part.PartitionSpec(arg))
        elif opt in ('-P'):
            pops.append(part.PartitionOptions(arg))
        else:
            pass
    if src and dst:
        return convertImage(src, dst, pspecs, pops)
    else:
        usage()
        return 2
