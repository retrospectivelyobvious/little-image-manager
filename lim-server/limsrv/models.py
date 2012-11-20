from django.db import models

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
