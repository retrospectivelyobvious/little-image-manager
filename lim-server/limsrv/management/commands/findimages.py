from django.core.management.base import BaseCommand, CommandError
from limsrv.models import Image

from limsrv import settings

import os
import hashlib
import littleimage as lim

#sys.path.append(settings.LIM_PATH)
#sys.stdout.write(str(sys.path))

class Command(BaseCommand):
    args = ''
    help = 'Generates an index of LIM Images on the server'

    def handle(self, *args, **options):
        for f in os.listdir(settings.IMGDIR_LOCAL):
            try:
                filepath = settings.IMGDIR_LOCAL + "/"+ f
                a = lim.Archive(filepath, src=True)
                meta = a.getMeta()
                fhash = hashlib.md5(file(filepath, 'rb').read()).hexdigest()
                #self.stdout.write(str(meta) + "\n")
                i = Image(filename=f, filehash=fhash, img_ver=meta['img_ver'], \
                          name=meta['name'], compression=meta['compression'], \
                          url=meta['url'], description=meta['description'], \
                          format_ver=meta['format_ver'], hw_ver=meta['hw_ver'])
                i.save()
            except lim.errors.BadArchive as ba:
                self.stdout.write("Invalid Archive: " + str(ba) + "\n")
        self.stdout.write("ABORT!\n")

