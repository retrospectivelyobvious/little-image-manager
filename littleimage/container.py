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

import support
import partition as part
import hardware as hw
import errors

class Container(object):
    def __init__(self):
        pass
    def tidy(self):
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
        self.dirt = []
        self.exchangeDir = tempfile.mkdtemp()
        self.dev = parted.Device(node)
        if(src):
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
        meta['format_ver'] = hw.LIM_VERSION
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

    def putGeom(self, partlist):
        #Write the disk geometry information
        #Template code @ https://bitbucket.org/rbistolfi/vinstall/wiki/pyparted
        disk = parted.freshDisk(self.dev, "msdos")
        for par in partlist:
            print (par.start, par.end)
            #TODO: should check that the geometry is within the disk
            g = parted.Geometry(device=self.dev, start=par.start, end=par.end)
            fs = parted.FileSystem(type=par.fstype, geometry=g)

            #TODO: eventually we should be able to handle logical/extended
            #partitions - right now it's primary only
            ptype = parted.PARTITION_NORMAL
            if par.parttype != 'primary':
                raise errors.partError(par.parttype)
                
            p = parted.Partition(disk=disk, fs=fs, type=ptype, geometry=g)
            c = parted.Constraint(exactGeom = g)
            disk.addPartition(partition=p, constraint=c)
        disk.commit()

        #refresh the OS's view of the disk
        support.partprobe(self.node)

        #put file systems onto the new partitions
        for par in partlist:
            support.mkfs(par.composeNode(self.node), par.fstype)
        #for par in partlist:
            

    def putMBR(self, mbrloc):
        support.dd(count=1, infile=mbrloc, outfile=self.node, bs=512)

    def getMBR(self):
        self.exchangeMBR = self.exchangeDir + "/MBR"
        support.dd(count=1, infile=self.dev.path, \
                   outfile=self.exchangeMBR)
        return self.exchangeMBR

    def getPartitions(self):
        partlist = []
        for par in self.disk.getPrimaryPartitions():
            p = part.DiskPartition(number=par.number, \
                              device=self.dev.path, \
                              startSec=par.geometry.start, \
                              size=par.geometry.length, \
                              exchangeDir=self.exchangeDir, \
                              parttype='primary',\
                              fs=par._fileSystem.type)
            partlist.append(p)
        self.partitions = partlist
        return partlist

    def putPartition(self, partition):
        number = partition[0]
        cfg = partition[1]
        loc = partition[2]
        print partition
        if cfg['storage'] == block:
            support.dd(count=cfg['size'], seek=cfg['start'], infile=loc, \
                       outfile=self.node, bs=512)
        if cfg['storage'] == tarball:
            support.createFS()
            support
            support.untar(loc)

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

    def getMeta(self):
        try:
            meta = self.extractFromConfig('meta')
            #Test for presence of all required fields
            m = meta['name']
            m = meta['compression']
            m = meta['url']
            m = meta['description']
            m = meta['img_ver']
            m = meta['format_ver']
            m = meta['hw_ver']
            return meta
        except KeyError as k:
            raise errors.BadArchive(self.ar, meta=str(k.args[0]))

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
                parts.append(part.ArchivePartition(number=number, \
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

class URL(Archive):
    def __init__(self, url):
        tempdir = tempfile.mkdtemp()
        f = os.path.basename(tempdir)
        (fname, header) = urllib.urlretrieve(url, tempdir + "/" + f)
        try:
            super(URL, self).__init__(fname, src=True)
        except:
            raise

    def __del__(self):
        pass

class RepoImage(object):
    def __init__(self, name, desc, filehash, url, compression, format_ver, \
                 img_ver, hw_ver, loc):
        self.name = name
        self.desc = desc
        self.filehash = filehash
        self.url = url
        self.compression = compression
        self.format_ver = format_ver
        self.img_ver = img_ver
        self.hw_ver = hw_ver
        self.loc = loc
    def __str__(self):
        s = "(" + str(self.hw_ver) + ") " + self.name + " - " + self.desc
        return s

class Repo(URL):
    def __init__(self, repoURL):
        repoxml = urllib.urlopen(repoURL)
        repodom = minidom.parse(repoxml)
        imgs = repodom.getElementsByTagName("image")
        imglist = []
        for img in imgs:
            rimage = RepoImage( \
                name = img.getElementsByTagName("name")[0].childNodes[0].data, \
                desc = img.getElementsByTagName("description")[0].childNodes[0].data, \
                filehash = img.getElementsByTagName("filehash")[0].childNodes[0].data, \
                url = img.getElementsByTagName("url")[0].childNodes[0].data, \
                img_ver = img.getElementsByTagName("img_ver")[0].childNodes[0].data, \
                hw_ver = img.getElementsByTagName("hw_ver")[0].childNodes[0].data, \
                compression = img.getAttribute("compression"), \
                format_ver = img.getAttribute("format_ver"), \
                loc = img.getAttribute("location"))
            print str(len(imglist)) + ") " + str(rimage)
            imglist.append(rimage)
        try:
            index = raw_input('Pick an Image: ')
            super(Repo, self).__init__( imglist[int(index)].loc )
        except:
            raise