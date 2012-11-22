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
