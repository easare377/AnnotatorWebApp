from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Projects)
admin.site.register(ImageInfo)
admin.site.register(AnnotationType)
admin.site.register(AnnotationSetup)
admin.site.register(ObjectClass)
admin.site.register(Polygons)
