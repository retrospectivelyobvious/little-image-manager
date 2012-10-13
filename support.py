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
