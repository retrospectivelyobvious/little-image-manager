from limsrv.models import Image
from django.http import HttpResponse

def index(request):
    return HttpResponse("Some text!")