from limsrv.models import Image
from django.http import HttpResponse
import xml.dom.minidom as minidom

def index(request):
    imgs = Image.objects.all()
    doc = minidom.Document()
    r = doc.createElement("LIM-Archive")
    doc.appendChild(r)
    for img in imgs:
        r.appendChild(img.dom())
    return HttpResponse(doc.toprettyxml())
