from django.contrib import admin
from .models import UploadedImage, Caption

# Register your models here.

admin.site.register(UploadedImage)
admin.site.register(Caption)
