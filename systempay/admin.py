from django.contrib import admin
from systempay import models


class SystemPayTransactionAdmin(admin.ModelAdmin):
    pass


admin.site.register(models.SystemPayTransaction, SystemPayTransactionAdmin)