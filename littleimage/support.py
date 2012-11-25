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

def dd(count, skip=0, seek=0, infile='/dev/zero', outfile='/dev/null', bs=512):
    return ddPopen(count, skip, seek, infile, outfile, bs, False)

def ddPopen(count, skip=0, seek=0, infile='/dev/zero', outfile='/dev/null', bs=512, process=True):
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

    if(process):
        return subprocess.Popen(call, stdin=infd, stdout=outfd)
    else:
        r = subprocess.call(call, stdin=infd, stdout=outfd)
        #shell truth (0=success) is inverted from normal (1=True) 
        if(r):
            raise errors.SubprocessError('dd', r)
        return True

def ar(archive, member, p, mod, stdin=None, stdout=None, stderr=None, process=False):
    call = ['ar', str(p) + str(mod), str(archive), str(member)]
    if(process):
        return subprocess.Popen(call, stdin=stdin, stdout=stdout, stderr=stderr)
    else:
        r = subprocess.call(call, stdin=stdin, stdout=stdout, stderr=stderr)
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
    nfd = open('/dev/null', 'wb')
    ar(archive, member, p='p', mod='D', stdout=efd, stderr=nfd)
    efd.close()
    nfd.close()
    return name

def tar(tarfile='/dev/null', target='/dev/zero', options='czf', cwd=None):
    call = ['tar', options, tarfile, target]
    p = subprocess.Popen(call, cwd=cwd)
    r = p.wait()
    if(r):
        raise errors.SubprocessError('tar', r)
    return True

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

def mkfs(device, fstype):
    opts = []
    if fstype == 'ext2':
        fsprog = 'mkfs.ext2'
    elif fstype == 'ext3':
        fsprog = 'mkfs.ext3'
    elif fstype == 'ext4':
        fsprog = 'mkfs.ext4'
    elif fstype == 'fat16':
        fsprog == 'mkfs.vfat'
        opts = ['F16']
    elif fstype == 'fat32':
        fsprog == 'mkfs.vfat'
        opts = ['F32']

    call = [fsprog]
    call.extend(opts)
    call.append(device)
    r = subprocess.call(call)
    if(r):
        raise errors.SubprocessError(fsprog, r)
    else:
        return True
