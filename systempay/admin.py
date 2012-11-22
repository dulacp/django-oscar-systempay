from django.contrib import admin
from systempay import models


class SystemPayTransactionAdmin(admin.ModelAdmin):
    list_display = ['mode', 'amount', 'currency', 'order_number', 'trans_id', 'trans_date',
                    'date_created']
    readonly_fields = [
        'mode',
        'amount',
        'currency',
        'order_number',
        'result',
        'auth_result',
        'trans_id',
        'trans_date',
        'error_message',
        'raw_request',
        'date_created',
        'computed_signature',
        'request'
    ]


admin.site.register(models.SystemPayTransaction, SystemPayTransactionAdmin)