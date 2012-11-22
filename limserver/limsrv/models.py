from django.db import models
import xml.dom.minidom as minidom
from limsrv import settings

impl =  minidom.getDOMImplementation()

class Image(models.Model):
    filename = models.CharField(max_length=100)
    filehash = models.CharField(max_length=33)

    name = models.CharField(max_length=25)
    description = models.CharField(max_length=500)
    url = models.CharField(max_length=500)
    compression = models.CharField(max_length=10)

    img_ver = models.DecimalField(max_digits=5, decimal_places=2, )
    format_ver = models.DecimalField(max_digits=5, decimal_places=2)
    hw_ver = models.IntegerField()

    def __str__(self):
        s = str(self.name) + " (" + str(self.img_ver) + "/" + str(self.filename)\
            + ")" + " " + str(self.description)
        return s

    def dom(self):
        doc = minidom.Document()
        n = doc.createElement("image")
        n.setAttribute("format_ver", str(self.format_ver))
        n.setAttribute("compression", self.compression)
        n.setAttribute("location", settings.IMGDIR_URI + self.filename)

        e = doc.createElement("name")
        e.appendChild(doc.createTextNode(self.name))
        n.appendChild(e)

        e = doc.createElement("description")
        e.appendChild(doc.createTextNode(self.description))
        n.appendChild(e)

        e = doc.createElement("img_ver")
        e.appendChild(doc.createTextNode(str(self.img_ver)))
        n.appendChild(e)

        e = doc.createElement("hw_ver")
        e.appendChild(doc.createTextNode(str(self.hw_ver)))
        n.appendChild(e)

        e = doc.createElement("filehash")
        e.appendChild(doc.createTextNode(self.filehash))
        n.appendChild(e)

        e = doc.createElement("url")
        e.appendChild(doc.createTextNode(self.url))
        n.appendChild(e)

        return n
