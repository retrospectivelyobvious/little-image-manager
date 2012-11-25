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

""" This file is the global magic number definition for LIM. It contains the
mappings between hardware/revisions and their identifying numeric constants
"""

LIM_VERSION = 0.1

class limage:
    def __init__(self, shortname, fullName, idnum):
        self.shortname = shortname
        self.desc = fullName
        self.idnum = idnum
        self.children = {}
        self.images = []

    def addChild(self, child):
        self.children[child.shortname] = child

    def selections(self, parentName):
        fullname = ''
        if parentName == '' or parentName == 'None':
            #if we're the first level in the tree
            fullname = self.shortname
        else:
            #any other level in the tree
            fullname = parentName + "." + self.shortname

        block = str(self.idnum) + " : " + fullname  +  " - " + self.desc

        for key, val in self.children.items():
            childblock = val.selections(fullname)
            block = block + '\n'+ childblock
        return block

hw = limage('None', 'Board Unspecified', 0)
hw.addChild( limage('Beagle', "Generic Beagle Bone/Board", 1) )
hw.addChild( limage('RaspberryPi', "Original Raspberry Pi", 2) )
hw.children['Beagle'].addChild( limage('BeagleBone', "The Beagle Bone", 3) )

if __name__ == "__main__":
    print hw.selections('')
