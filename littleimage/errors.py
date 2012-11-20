import os

class BadArchive(Exception):
    def __init__(self, archive, member=None):
        self.archive = os.path.normpath(archive)
        self.name = os.path.basename(archive)
        self.path = os.path.dirname(archive)
        self.member = member

    def __str__(self):
        if(self.member):
            return self.name + ", " + "Missing Member: " + self.member
        else:
            return self.name
