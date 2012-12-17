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

import partition as limpartition
import container

"""
The functionality in this submodule is the client half of a client/server
system image retrieval repository.
"""

class URL(container.Archive):
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


