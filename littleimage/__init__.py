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
import partition as part
import hardware as hw

def convertImage(fromLoc, toLoc, partSpecs):
    meta = fromLoc.getMeta()
    try:
        if float(meta['format_ver']) != float(hw.LIM_VERSION):
            print "The source (" + str(meta['format_ver']) + ") " \
                  + "was not created with this version of LIM (" + \
                  str(hw.LIM_VERSION) + ")."
            print "It is not safe to continue - bailing."
            return 3
    except:
        return 3

    toLoc.putMeta(meta)
    toLoc.putDisk(fromLoc.getDisk())

    #read partition specifiers from archive
    #override any parts specified on command line (warn about shrinkage or
    #   shifted start points)
    #write MBR
    # for each partition pair
    #    dest(geometry info, fs type info,
    #    src( writeTar(geometry info, fs type info), writeBlock() )
    #    dest.write(src, write(Tar/Block))

    #create any needed file systems
    #write FS partitions
    #write block-device partitions

    #try to create block devices sized to part specifiers
    #toLoc.putMBR(fromLoc.getMBR())
    parts = fromLoc.getPartitions()
    parts = part.adjustPartitions(parts, partSpecs)
    toLoc.putGeom(parts)
    raise "breakage"
    for par in parts:
        toLoc.putPartition(par.getBlock())

    toLoc.finalize()

def usage():
    print("Little Image Manager (LIM)")
    print("Usage:")
    print("-d, -a <file> : Specify source device (-d) or source archive (-a)")
    print("-u <URL> : Specify a source URL at which an archive is located")
    print("-r <URL> : Specify a source URL at which a repository manifest is located")
    print("-D, -A <file> : Specify destination device (-D) or destination archive (-A)")

def main(argv):
    try:
        opts, leftover = getopt.getopt(argv[1: ], 'd:a:u:r:D:A:p:',
                                                          ['src-device=',
                                                           'src-archive=',
                                                           'src-url=',
                                                           'src-repo=',
                                                           'dst-device=',
                                                           'dst-archive=',
                                                           'config=',
                                                           'partition='])
    except getopt.GetoptError:
        print "Invalid Options: "
        print "Usage!!"
        return 1

    src = None
    dst = None
    pops = []
    for opt,arg in opts:
        if   opt in ('-d', '--src-device'):
            if(src):
                raise "May not have more than one source."
            src = container.BlockDevice(arg, src=True)
        elif opt in ('-D', '--dst-device'):
            if(dst):
                raise "May not have more than one destination."
            dst = container.BlockDevice(arg)
        elif opt in ('-a', '--src-archive'):
            if(src):
                raise "May not have more than one source."
            src = container.Archive(arg, src=True)
        elif opt in ('-u', '--src-url'):
            if(src):
                raise "May not have more than one source."
            src = container.URL(arg)
        elif opt in ('-r', '--src-repo'):
            if(src):
                raise "May not have more than one source."
            src = container.Repo(arg)
        elif opt in ('-A', '--dst-archive'):
            if(dst):
                raise "May not have more than one destination."
            dst = container.Archive(arg)
        elif opt in ('-p', '--partition'):
            pops.append(part.PartitionSpec(arg))
        else:
            pass
    if src and dst:
        return convertImage(src, dst, pops)
    else:
        usage()
        return 2
