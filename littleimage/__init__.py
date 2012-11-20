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

import subprocess
import getopt
import shutil
import re

import ConfigParser
import tempfile
import parted

import support
import hardware as hw

LIM_VERSION = 0.1

def convertImage(fromLoc, toLoc):
#    print fromLoc.getMeta()
#    print fromLoc.getDisk()
#    print fromLoc.getMBR()
#    for part in fromLoc.getPartitions():
#        print part.get()
#    return 0
    meta = fromLoc.getMeta()
    try:
        if meta['format_ver'] != LIM_VERSION:
            print "The source was not created with this version of LIM."
            print "It is not safe to continue - bailing."
            return 3
    except:
        return 3
    toLoc.putMeta(meta)
    toLoc.putDisk(fromLoc.getDisk())
    toLoc.putMBR(fromLoc.getMBR())

    for part in fromLoc.getPartitions():
        print part
        toLoc.putPartition(part.get())

    toLoc.finalize()

class Image():
    def __init__(self):
        pass
    def tidy(self):
        pass
    def putMeta(self, meta):
        pass
    def putDisk(self, disk):
        pass

class Partition():
    def __init__(self):
        pass
#    def tidy():
#        while self.dirt:
#            d = self.dirt.pop(0)
#            os.system('rm ' + d)

class BlockDevice(Image):
    def __init__(self, node, src=False):
        self.node = node
        self.dirt = []
        self.exchangeDir = tempfile.mkdtemp()
        if(src):
            self.dev = parted.Device(node)
            self.disk = parted.Disk(self.dev)

    def tidy():
        while self.dirt:
            d = self.dirt.pop(0)
            os.system('rm ' + d)
        try:
            for p in self.partitions:
                p.tidy()
        except:
            raise

    def getMeta(self):
        meta = {}
        meta['name'] = raw_input('Name: ')
        meta['description'] = raw_input('Description: ')
        meta['url'] = raw_input('URL: ')
        meta['compression'] = 'gzip'
        meta['img_ver'] = raw_input('Image Version: ')
        meta['format_ver'] = LIM_VERSION
        print "Identify the hardware version:"
        print hw.hw.selections('')
        meta['hw_ver'] = raw_input('HW ID Number: ')
        return meta

    def getDisk(self):
        disk = {}
        disk['geometry'] = self.dev.hardwareGeometry
        disk['logical_sector_size'] = self.dev.sectorSize
        disk['physical_sector_size'] = self.dev.physicalSectorSize
        disk['type'] = self.disk.type  #msdos, gpt, etc
        return disk

    def putMBR(self, mbrloc):
        support.dd(count=1, infile=mbrloc, outfile=self.node, bs=512)

    def getMBR(self):
        self.exchangeMBR = self.exchangeDir + "/MBR"
        support.dd(count=1, infile=self.dev.path, \
                   outfile=self.exchangeMBR)    
        return self.exchangeMBR

    def getPartitions(self):
        partlist = []
        for part in self.disk.getPrimaryPartitions():
            p = BlockPartition(number=part.number, \
                               device=self.dev.path, \
                               startSec=part.geometry.start, \
                               size=part.geometry.length, \
                               exchangeDir=self.exchangeDir, \
                               parttype='primary',\
                               fs=part._fileSystem.type)
            partlist.append(p)
        self.partitions = partlist
        return partlist

    def putPartition(self, partition):
        number = partition[0]
        cfg = partition[1]
        loc = partition[2]
        print partition
        support.dd(count=cfg['size'], seek=cfg['start'], infile=loc, \
                   outfile=self.node, bs=512)

    def finalize(self):
        pass

class BlockPartition(Partition):
    def __init__(self, number, device, startSec, size, exchangeDir, \
                 parttype, fs):
        self.number = number    #the partition number /dev/sda1 = 1
        #self.node = node        #the file path to the partition '/dev/sda1'
        self.device = device    #the path to the parted block device '/dev/sda'
        self.startSec = startSec #sector number at which the partition starts
        self.size = size        #length of the partition in sectors
        self.exchangeDir = exchangeDir
        self.parttype = parttype
        self.fs = fs

    def tidy(self):
        if self.exchangeFile:
            self.exchangeFile.close()

    def get(self):
        self.exchangeFile = self.exchangeDir + "/p" + str(self.number)
        p = support.ddPopen(count=self.size, skip=self.startSec, \
                            infile=self.device, \
                            outfile=subprocess.PIPE)
        efd = open(self.exchangeFile, 'w+b')
        subprocess.call(['gzip', '-c', '--best'], stdin=p.stdout, stdout=efd)
        efd.close()

        #partition is a tuple of (number, config_info, exchangefilelocation)
        config = {'start':self.startSec, 'size':self.size, \
                  'type':self.parttype,  'filesystem':self.fs}
        return (self.number, config, self.exchangeFile)

class Archive(Image):
    def __init__(self, node, src=False):
        self.config = ConfigParser.ConfigParser()
        self.ar = node
        if(src):
            self.exchangeDir = tempfile.mkdtemp()
            confFile = support.arGet(self.ar, 'meta', self.exchangeDir)
            self.config.read(confFile)

    def addFile(self, fileloc):
        support.arAdd(self.ar, fileloc)

    def putMeta(self, metainfo):
        self.addToConfig('meta', metainfo)

    def getMeta(self):
        try:
            meta = self.extractFromConfig('meta')
            #Test for preseence of all required fields
            m = meta['name']
            m = compression=meta['compression']
            m = meta['url']
            m = description=meta['description']
            m = img_ver=meta['img_ver']
            m = meta['format_ver']
            m = meta['hw_ver']
            return meta
        except KeyError as k:
            raise errors.BadArchive(self.ar, member=str(k.args[0]))

    def putDisk(self, diskinfo):
        self.addToConfig('disk', diskinfo)

    def getDisk(self):
        return self.extractFromConfig('disk')

    def putMBR(self, mbrloc):
        self.addFile(mbrloc)

    def getMBR(self):
        return support.arGet(self.ar, 'MBR', self.exchangeDir)

    def putPartition(self, partition):
        #partition is a tuple of (number, config_info, exchangefilelocation)
        number = partition[0]
        self.addToConfig('p' + str(number), partition[1])
        self.addFile(partition[2])

    def getPartitions(self):
        exp = re.compile('p[0-9]+')
        parts = []
        for s in self.config.sections():
            if exp.match(s):
                number = s[1:]
                cfginfo = self.extractFromConfig(s)
                parts.append(ArchivePartition(number=number, \
                                              archive=self.ar, \
                                              startSec=cfginfo['start'],\
                                              size=cfginfo['size'],\
                                              exchangeDir=self.exchangeDir,\
                                              parttype=cfginfo['type'],\
                                              fs=cfginfo['filesystem']))
        return parts

    def addToConfig(self, sectionName, sectionData):
        self.config.add_section(sectionName)
        for (key, value) in sectionData.items():
            self.config.set(sectionName, str(key), str(value))

    def extractFromConfig(self, sectionName):
        section = {}
        for (key,value) in self.config.items(str(sectionName)):
            section[key] = value
        return section

    def finalize(self):
        tempdir = tempfile.mkdtemp()
        metafile = tempdir + '/meta'
        with open(metafile, 'wb') as configfile:
            self.config.write(configfile)
        self.addFile(metafile)
        shutil.rmtree(tempdir)

class ArchivePartition(Partition):
    def __init__(self, number, archive, startSec, size, exchangeDir, parttype, fs):
        self.number = int(number)
        self.ar = archive
        self.startSec = startSec
        self.size = size
        self.exchangeDir = exchangeDir
        self.parttype = parttype
        self.fs = fs

    def get(self):
        self.exchangeFile = self.exchangeDir + "/p" + str(self.number)
        fd = support.arStream(self.ar, 'p' + str(self.number))
        efd = open(self.exchangeFile, 'w+b')
        subprocess.call(['gzip', '-d', '-c'], stdin=fd, \
                        stdout=efd)
        efd.close()

        config = {'start':self.startSec, 'size':self.size, \
                  'type':self.parttype,  'filesystem':self.fs}
        return (self.number, config, self.exchangeFile)

def usage():
    print("Little Image Manager (LIM)")
    print("Usage:")
    print("-d, -a <file> : Specify source device (-d) or source archive (-a)")
    print("-D, -A <file> : Specify destination device (-D) or destination archive (-A)")

#'main' class, governs program operation
def main(argv):
    try:
        opts, leftover = getopt.getopt(argv[1: ], 'd:a:D:A:', 
                                                          ['src-device=',
                                                           'src-archive=',
                                                           'dst-device=',
                                                           'dst-archive=',
                                                           'config='])
    except getopt.GetoptError:
        print "Invalid Options: " 
        print "Usage!!"
        return 1

    src = None
    dst = None
    for opt,arg in opts:
        if   opt in ('-d', '--src-device'):
            if(src):
                raise "May not have more than one source."
            src = BlockDevice(arg, src=True) 
        elif opt in ('-D', '--dst-device'):
            if(dst):
                raise "May not have more than one destination."
            dst = BlockDevice(arg) 
        elif opt in ('-a', '--src-archive'):
            if(src):
                raise "May not have more than one source."
            src = Archive(arg, src=True) 
        elif opt in ('-A', '--dst-archive'): 
            if(dst):
                raise "May not have more than one destination."
            dst = Archive(arg) 
        #elif opt in ('-c', '--config'): 
        #    self.config = Config(arg) 
        else:
            pass
    if src and dst:
        return convertImage(src, dst)
    else:
        usage()
        return 2
