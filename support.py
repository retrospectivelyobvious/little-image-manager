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
            raise "Hell"
        return True

def ar(archive, member, p, mod, stdin=None, stdout=None, process=False):
    call = ['ar', str(p) + str(mod), str(archive), str(member)]
    if(process):
        return subprocess.Popen(call, stdin=stdin, stdout=stdout)
    else:
        return subprocess.call(call, stdin=stdin, stdout=stdout)

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
