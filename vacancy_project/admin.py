from django.contrib import admin
from django.contrib.auth.models import Group

# Configuring admin headers
admin.site.site_header = "Адміністрування Vacancy Project"
admin.site.site_title = "Vacancy Project"
admin.site.index_title = "Керування користувачами"

admin.site.unregister(Group)