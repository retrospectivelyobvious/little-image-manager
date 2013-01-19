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

import parted
import tempfile
import os
import re
import ConfigParser
import xml.dom.minidom as minidom
import urllib
import shutil

import subprocess
import support
import partition as limpartition
import hardware as hw
import errors

class Container(object):
    def __init__(self):
        pass

    def __del__(self):
        try:
            if self.exchangeDir:
                for root, dirs, files in os.walk(self.exchangeDir,
                                                 topdown=False):
                    for f in files:
                        os.remove(os.path.join(root, f))
                    for d in dirs:
                        os.rmdir(os.path.join(root, d))
                os.rmdir(self.exchangeDir)
        except:
            pass

    def putMeta(self, meta):
        pass
    def putDisk(self, disk):
        pass
    def putGeom(self, geom):
        pass

class BlockDevice(Container):
    def __init__(self, node, src=False):
        self.node = node
        self.exchangeDir = tempfile.mkdtemp()
        self.dev = parted.Device(node)
        if(src):
            self.disk = parted.Disk(self.dev)

    def getMeta(self, compress, needmeta=True):
        meta = {}
        if needmeta:
            meta['name'] = raw_input('Name: ')
            meta['description'] = raw_input('Description: ')
            meta['url'] = raw_input('URL: ')
            meta['img_ver'] = raw_input('Image Version: ')
            #print "Identify the hardware version:"
            #print hw.hw.selections('')
            #meta['hw_ver'] = raw_input('HW ID Number: ')
        else:
            meta['name'] = ''
            meta['description'] = ''
            meta['url'] = ''
            meta['img_ver'] = 0
            #meta['hw_ver'] = 0
        meta['compression'] = compress
        meta['format_ver'] = hw.LIM_VERSION
        return meta

    def getDisk(self):
        disk = {}
        disk['geometry'] = self.dev.hardwareGeometry
        disk['logical_sector_size'] = self.dev.sectorSize
        disk['physical_sector_size'] = self.dev.physicalSectorSize
        disk['type'] = self.disk.type  #msdos, gpt, etc
        return disk

    def putGeom(self, limPartList):
        #Write the disk geometry information
        #Template code @ https://bitbucket.org/rbistolfi/vinstall/wiki/pyparted
        disk = parted.freshDisk(self.dev, "msdos")
        for lpar in limPartList:
            if lpar.parttype != 'artificial':
                #TODO: should check that the geometry is within the disk
                g = parted.Geometry(device=self.dev, start=lpar.start, end=lpar.end)
                fs = parted.FileSystem(type=lpar.fstype, geometry=g)

                #TODO: eventually we should be able to handle logical/extended
                #partitions - right now it's primary only
                ptype = parted.PARTITION_NORMAL
                if lpar.parttype != 'primary':
                    raise errors.partError(lpar.parttype)

                p = parted.Partition(disk=disk, fs=fs, type=ptype, geometry=g)
                c = parted.Constraint(exactGeom = g)
                disk.addPartition(partition=p, constraint=c)
                setFlags(p, lpar.flags)
        disk.commit()

        #refresh the OS's view of the disk
        support.partprobe(self.node)

        #put file systems onto the new partitions
        for lpar in limPartList:
            if lpar.parttype != 'artificial':
                support.mkfs(lpar.composeNode(self.node), lpar.fstype)

    def putMBR(self, mbrloc, codeonly=False):
        #if we've rewritten the partition table, we only want to copy in the
        #bootstrap code from the original MBR, which is on bytes [0, 444]
        if codeonly:
            support.dd(count=1, infile=mbrloc, outfile=self.node, bs=445)
        else:
            support.dd(count=1, infile=mbrloc, outfile=self.node, bs=512)

    def getMBR(self):
        self.exchangeMBR = os.path.join(self.exchangeDir, "MBR")
        support.dd(count=1, infile=self.dev.path, \
                   bs=512, outfile=self.exchangeMBR)
        return self.exchangeMBR

    def getPartFlags(self, parted_part):
        #if you make changes here, also update partition.buildConfig
        boot = parted_part.getFlag(parted.PARTITION_BOOT)
        lba = parted_part.getFlag(parted.PARTITION_LBA)
        lvm = parted_part.getFlag(parted.PARTITION_LVM)
        flags = {'boot':boot, 'lba':lba, 'lvm':lvm}
        return flags

    def getLimPartitions(self):
        lim_partlist = []
        for parted_part in self.disk.getPrimaryPartitions():
            p = limpartition.DiskPartition(number=parted_part.number, \
                              device=self.dev.path, \
                              startSec=parted_part.geometry.start, \
                              size=parted_part.geometry.length, \
                              exchangeDir=self.exchangeDir, \
                              parttype='primary', \
                              fs=parted_part._fileSystem.type, \
                              msdoslabel=support.readPartID(self.dev.path, parted_part.number), \
                              flags=self.getPartFlags(parted_part))
            lim_partlist.append(p)
        #get 'partition 0', the interstitial stuff between MBR and p1
        if lim_partlist[0].startSec > 1:
            p = limpartition.DiskPartition(number=0, \
                                   device=self.dev.path, \
                                   startSec=1, \
                                   size=lim_partlist[0].startSec-1, \
                                   exchangeDir=self.exchangeDir, \
                                   parttype='artificial', \
                                   fs=None, \
                                   msdoslabel=0, \
                                   flags={}, \
                                   storage='block')
            lim_partlist.append(p)
        self.partitions = lim_partlist
        return lim_partlist

    def putPartition(self, exchangeDesc, compress):
        number = exchangeDesc.number
        cfg = exchangeDesc.config
        loc = exchangeDesc.exchangeloc
        if cfg['storage'] == 'block':
            support.dd(count=cfg['size'], seek=cfg['start'], infile=loc, \
                       outfile=self.node, bs=512)
            #TODO - Do you need to restore the disk label byte for a block put
        if cfg['storage'] == 'tarball':
            #TODO - Migrage the partition creation code here
            #support.createFS()
            self.mountDir = os.path.join(self.exchangeDir, \
                                         "mount" + str(number))
            os.mkdir(self.mountDir)
            support.mount(device=self.node + str(number), dest=self.mountDir)

            #Extract the exchange file to the new partition
            efd = open(loc, 'r')
            #tarp = support.tarExtract_Process(self.mountDir)
            #subprocess.call(compress.getDecompressOpts(),
            #                stdin=efd, stdout=tarp.stdin)
            q = subprocess.Popen(compress.getDecompressOpts(), stdin=efd,
                             stdout=subprocess.PIPE)
            p = support.tarExtract_Process(self.mountDir, stdin=q.stdout)
            p.wait()
            q.wait()
            efd.close()
            #support.tar(tarfile=loc, target='', options='xzf', \
            #            cwd=self.mountDir)

            support.umount(self.mountDir)
            support.writePartID(self.node, number, int(cfg['label']))

    def finalize(self):
        pass

class Archive(Container):
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

    def getMeta(self, compress, needmeta=True):
        try:
            meta = self.extractFromConfig('meta')
            #Test for presence of all required fields
            m = meta['name']
            m = meta['compression']
            m = meta['url']
            m = meta['description']
            m = meta['img_ver']
            m = meta['format_ver']
            #m = meta['hw_ver']
            return meta
        except KeyError as k:
            raise errors.BadArchive(self.ar, meta=str(k.args[0]))

    def putDisk(self, diskinfo):
        self.addToConfig('disk', diskinfo)

    def getDisk(self):
        return self.extractFromConfig('disk')

    def putMBR(self, mbrloc, codeonly=False):
        self.addFile(mbrloc)

    def getMBR(self):
        return support.arGet(self.ar, 'MBR', self.exchangeDir)

    def putPartition(self, exchangeDesc, compress):
        number = exchangeDesc.number
        self.addToConfig('p' + str(number), exchangeDesc.config)
        self.addFile(exchangeDesc.exchangeloc)

    def getPartFlags(self, partflags):
        #if you make changes here, also update partition.buildConfig
        #TODO convert config file flags string into a dict of flags
        #TODO support all flags
        flags = {'boot':False, 'lba':False, 'lvm':False}
        cfgflags = partflags.split(':')
        for f in cfgflags:
            try:
                flags[f] = True
            except KeyError:
                pass
        return flags

    def getLimPartitions(self):
        exp = re.compile('p[0-9]+')
        parts = []
        for s in self.config.sections():
            if exp.match(s):
                number = s[1:]
                cfginfo = self.extractFromConfig(s)
                parts.append(limpartition.ArchivePartition(number=number, \
                                          archive=self.ar, \
                                          startSec=cfginfo['start'],\
                                          size=cfginfo['size'],\
                                          exchangeDir=self.exchangeDir,\
                                          parttype=cfginfo['type'],\
                                          fs=cfginfo['filesystem'],\
                                          msdoslabel=cfginfo['label'],\
                                          flags=self.getPartFlags(cfginfo['flags']),
                                          storage=cfginfo['storage']))
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

def setFlags(partedPartition, partFlags):
    if partFlags['boot']:
        partedPartition.setFlag(parted.PARTITION_BOOT)
    if partFlags['lba']:
        partedPartition.setFlag(parted.PARTITION_LBA)
    if partFlags['lvm']:
        partedPartition.setFlag(parted.PARTITION_LVM)
