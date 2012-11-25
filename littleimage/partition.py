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
    def __init__(self, number, start, size, fstype, parttype=None, \
                 device=None):
        self.number = int(number) #the partition number /dev/sda1 = 1
        self.start = int(start) #location at which the partition starts (in sectors)
        self.size = int(size) #length of the partition (in sectors)
        self.fstype = str(fstype) 
        self.parttype = parttype  #'primary' or 'extended', None -> no override 
        self.device = device    #the path to the parted block device '/dev/sda'

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

    def composeNode(self, root):
        return root + str(self.number)

    def __str__(self):
        s = "Partition " + str(self.number) + ": [" + str(self.start) + ", " \
            + str(self.start + self.size) + "]s" + " " + self.fstype
        return s

class PartitionSpec(Partition):
    #partition options are in the format of -pN:start:len:units:fstype
    # N is partition number
    # start is the start of the partition
    # len is the size of the partition
    # units are the units that start & end are specified in
    # fstype is the file system type
    # start, end, units, and fstype should be in notation understood by the
    #     'parted' program
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

class DiskPartition(Partition):
    def __init__(self, number, device, startSec, size, exchangeDir, \
                 parttype, fs):
        super(DiskPartition, self).__init__(\
            number = number, \
            start = startSec, \
            size = size, \
            fstype = fs, \
            parttype = parttype, \
            device = device)
        self.exchangeDir = exchangeDir

    #def __del__(self):
    #    if self.exchangeFile:
    #       self.exchangeFile.close()
    #       support.rm(self.exchangeFile)

    def getBlock(self):
        self.exchangeFile = self.exchangeDir + "/p" + str(self.number)
        p = support.ddPopen(count=self.size, skip=self.startSec, \
                            infile=self.device, \
                            outfile=subprocess.PIPE)
        efd = open(self.exchangeFile, 'w+b')
        subprocess.call(['gzip', '-c', '--best'], stdin=p.stdout, stdout=efd)
        efd.close()

        #partition is a tuple of (number, config_info, exchangefilelocation)
        config = {'start':self.startSec, 'size':self.size, \
                  'type':self.parttype,  'filesystem':self.fstype, \
                  'storage':'block'}
        return (self.number, config, self.exchangeFile)

    def getTarball(self):
        self.exchangeFile = self.exchangeDir + "/p" + str(self.number)

        self.mountDir = self.exchangeDir + "/mount" + str(self.number)
        os.mkdir(self.mountDir)
        support.mount(device=self.device + str(self.number), dest=self.mountDir)
        support.tar(tarfile=self.exchangeFile, target='.', options='czf', \
                    cwd=self.mountDir)
        support.umount(self.mountDir)

        #partition is a tuple of (number, config_info, exchangefilelocation)
        config = {'start':self.startSec, 'size':self.size, \
                  'type':self.parttype,  'filesystem':self.fstype, \
                  'storage':'tarball'}
        return (self.number, config, self.exchangeFile)

class ArchivePartition(Partition):
    def __init__(self, number, archive, startSec, size, exchangeDir, parttype, fs):
        super(ArchivePartition, self).__init__(\
            number=number, \
            start=startSec, \
            size=size, \
            parttype=parttype, \
            fstype=fs)

        self.exchangeDir = exchangeDir
        self.ar = archive

    def getBlock(self):
        self.exchangeFile = self.exchangeDir + "/p" + str(self.number)
        fd = support.arStream(self.ar, 'p' + str(self.number))
        efd = open(self.exchangeFile, 'w+b')
        subprocess.call(['gzip', '-d', '-c'], stdin=fd, \
                        stdout=efd)
        efd.close()

        config = {'start':self.startSec, 'size':self.size, \
                  'type':self.parttype,  'filesystem':self.fstype}
        return (self.number, config, self.exchangeFile)

def adjustPartitions(partlist, partspecs):
    #TODO - need some significant sanity checking here
    for p in partlist:
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
    return partlist