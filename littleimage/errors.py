import os

class BadArchive(Exception):
    def __init__(self, archive, member=None, meta=None):
        self.archive = os.path.normpath(archive)
        self.name = os.path.basename(archive)
        self.path = os.path.dirname(archive)
        self.member = member
        self.meta = meta

    def __str__(self):
        if(self.meta):
            return self.name + ", " + "Missing MetaInfo: " + self.meta
        else:
            return self.name

class UnitsError(Exception):
    def __init__(self, unitname):
        self.unitname = unitname

    def __str__(self):
        return "Bad Units: " + str(unitname)

class PartitionError(Exception):
    def __init__(self, parttype):
        self.parttype = parttype

    def __str__(self):
        return "Partition Type, " + str(parttype) + ", is not type 'primary'"

class SubprocessError(Exception):
    def __init__(self, processname, errorcode=None):
        self.processname = processname
        self.errorcode = errorcode

    def __str__(self):
        s = "Subprocess " + str(processname) + " failed"
        if self.errorcode:
            s += " with error code: " + str(errorcode)
        return s
