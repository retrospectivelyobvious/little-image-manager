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
import errors

class Compress(object):
    def __init__(self, comptype):
        if comptype in ('gzip', 'bzip', 'xz'):
            self.comptype = comptype
        else:
            raise Exception("Invalid Compression Type: " + comptype)

    def getCompressOpts(self):
        if self.comptype == 'gzip':
            return ['gzip', '-c', '--best']
        elif self.comptype == 'bzip':
            return ['bzip2', '-c', '--best']
        elif self.comptype == 'xz':
            return ['xz', '-c', '--best']

    def getDecompressOpts(self):
        if self.comptype == 'gzip':
            return ['gzip', '-d', '-c']
        elif self.comptype == 'bzip':
            return ['bzip2', '-d', '-c']
        elif self.comptype == 'xz':
            return ['xz', '-d', '-c']

def dd(count, skip=0, seek=0, infile='/dev/zero', outfile='/dev/null', bs=512):
    p = ddPopen(count, skip, seek, infile, outfile, bs)
    #shell truth (0=success) is inverted from normal (1=True)
    r = p.wait()
    if(r):
        raise errors.SubprocessError('dd', r)
    return True

def ddPopen(count, skip=0, seek=0, infile='/dev/zero', outfile='/dev/null', \
            bs=512, dbg=False):
    call = ['dd', 'count=' + str(count) ]
    infd = None
    outfd = None
    if(skip):
        call.append('skip=' + str(skip))
    if(seek):
        call.append('seek=' + str(seek))
    if(bs):
        call.append('bs=' + str(bs))

    if(infile):
        if isinstance(infile, str):
            call.append('if=' + infile)
        if isinstance(infile, int):
            infd = infile
        if infile == subprocess.PIPE:
            infd = subprocess.PIPE
        try:
            if isinstance(infile.file, file):
                infd = infile
        except:
            pass

    if(outfile):
        if isinstance(outfile, str):
            call.append('of=' + outfile)
        if isinstance(outfile, int):
            outfd = outfile
        if outfile == subprocess.PIPE:
            outfd = subprocess.PIPE
        try:
            if isinstance(outfile.file, file):
                outfd = outfile
        except:
            pass

    stderr = None
    if not dbg:
        null = open('/dev/null', 'w')
        stderr = null

    return subprocess.Popen(call, stdin=infd, stdout=outfd, stderr=null)

def ar(archive, member, p, mod, stdin=None, stdout=None, \
       process=False, dbg=False):
    call = ['ar', str(p) + str(mod), str(archive), str(member)]

    stdo=stdout
    stderr=None
    null = 0
    if not dbg:
        null = open('/dev/null','w')
        stdo = null
        stderr = null

    if(process):
        return subprocess.Popen(call, stdin=stdin, stdout=stdout, stderr=stderr)
    else:
        r = subprocess.call(call, stdin=stdin, stdout=stdout, stderr=stderr)
        if not dbg:
            null.close()
        if r != 0:
            # 1 == ar return code for 'unrecognized format'
            # 9 == ar return code for 'no such file'
            raise errors.BadArchive(archive)
        return r

def arAdd(archive, member):
    return ar(archive, member, p='r', mod='D')

def arStream(archive, member):
    p = ar(archive, member, p='p', mod='D', stdout=subprocess.PIPE, process=True)
    return p.stdout
    #return p.communicate()[0]

def arGet(archive, member, getDir):
    name = getDir + '/' + str(member)
    efd = open(name, 'wb')
    ar(archive, member, p='p', mod='D', stdout=efd)
    efd.close()
    return name

def tarCreate_Process(srcdir, files='.', dbg=False):
    call = ['tar', 'c', files]

    stderr = None
    if not dbg:
        null = open('/dev/null','w')
        stderr = null

    return subprocess.Popen(call, cwd=srcdir, stdout=subprocess.PIPE,
                            stderr=stderr)

def tarExtract_Process(destdir, stdin=subprocess.PIPE, dbg=False):
    call = ['tar', 'x']

    stderr = None
    stdout = None
    if not dbg:
        null = open('/dev/null','w')
        stderr = null
        stdout = null

    return subprocess.Popen(call, cwd=destdir, stdin=stdin,
                            stdout=null, stderr=null)

def mount(device, dest):
    call = ['mount', device, dest]
    r = subprocess.call(call)
    if(r):
        raise errors.SubprocessError('mount', r)
    else:
        return True

def umount(mountpoint):
    call = ['umount', mountpoint]
    r = subprocess.call(call)
    if(r):
        raise errors.SubprocessError('umount', r)
    else:
        return True

def rm(target, options=''):
    call = ['rm', options, target]
    r = subprocess.call(call)
    if(r):
        raise errors.SubprocessError('rm', r)
    else:
        return True

def partprobe(device=''):
    call = ['partprobe', device]
    r = subprocess.call(call)
    if(r):
        raise errors.SubprocessError('partprobe', r)
    else:
        return True

def mkfs(device, fstype, dbg=False):
    opts = []
    if fstype == 'ext2':
        fsprog = 'mkfs.ext2'
    elif fstype == 'ext3':
        fsprog = 'mkfs.ext3'
    elif fstype == 'ext4':
        fsprog = 'mkfs.ext4'
    elif fstype == 'fat16':
        fsprog = 'mkfs.vfat'
        opts = ['-F16']
    elif fstype == 'fat32':
        fsprog = 'mkfs.vfat'
        opts = ['-F32']

    call = [fsprog]
    call.extend(opts)
    call.append(device)

    stdout=None
    stderr=None
    null = 0
    if not dbg:
        null = open('/dev/null','w')
        stdout = null
        stderr = null

    r = subprocess.call(call, stdout=stdout, stderr=stderr)

    if not dbg:
        null.close()

    if(r):
        raise errors.SubprocessError(fsprog, r)
    else:
        return True

def readPartID(device, partNum):
    partTableBase = 0x1BE
    IDlocOffset = 0x4
    partTableEntryLen = 0x10

    r = 0
    if partNum > 0:
        IDloc = partTableBase + (partNum-1)*partTableEntryLen + IDlocOffset

        fd = open(device, "r") #open read
        fd.seek(IDloc)
        r = ord(fd.read(1))
        fd.close()

    return r

def writePartID(device, partNum, id):
    partTableBase = 0x1BE
    IDlocOffset = 0x4
    partTableEntryLen = 0x10

    if id > 0:
        #http://en.wikipedia.org/wiki/Master_boot_record
        IDloc = partTableBase + (partNum-1)*partTableEntryLen + IDlocOffset

        fd = open(device, "r+b") #open read/write, no truncation
        fd.seek(IDloc)
        fd.write("%c" % id)
        fd.close()
