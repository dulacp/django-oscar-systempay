import urlparse

from django.db import models

CURRENCIES = (
        ('36', 'AUD'),
        ('036', 'AUD'),
        ('124', 'CAD'),
        ('156', 'CNY'),
        ('208', 'DKK'),
        ('392', 'YEN'),
        ('578', 'NOK'),
        ('752', 'SEK'),
        ('756', 'CHF'),
        ('826', 'GBP'),
        ('840', 'USD'),
        ('953', 'CFP'),
        ('978', 'EUR'),
    )


class SystemPayTransaction(models.Model):

    # Mode (send or return) request
    MODE_SUBMIT, MODE_RETURN = ('Submit', 'Return')
    MODE_CHOICES = (
            (MODE_SUBMIT, u"Submit Request"),
            (MODE_RETURN, u"Return Request"),
        )
    mode = models.CharField(max_length=10, choices=MODE_CHOICES)

    OPERATION_TYPE_NONE, OPERATION_TYPE_DEBIT, OPERATION_TYPE_CREDIT = ('', 'DEBIT', 'CREDIT')
    OPERATION_TYPE_CHOICES = (
            (OPERATION_TYPE_NONE, ''),            
            (OPERATION_TYPE_DEBIT, 'DEBIT'),
            (OPERATION_TYPE_CREDIT, 'CREDIT'),
        )
    operation_type = models.CharField(max_length=10, choices=OPERATION_TYPE_CHOICES, blank=True, null=True)

    # Unique identifier in the range 000000 to 899999. Integer between 900000 and 999999 are reserved
    # NB: it should only be unique over the current day
    trans_id = models.CharField(max_length=6, blank=True, null=True)

    # Need to respect the format ``YYYYMMDDHHMMSS`` in UTC timezone
    trans_date = models.CharField(max_length=14, blank=True, null=True)

    order_number = models.CharField(max_length=127, blank=True, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    currency = models.CharField(max_length=8, blank=True, null=True)

    auth_result = models.CharField(max_length=2, blank=True, null=True)
    result = models.CharField(max_length=2, blank=True, null=True)

    error_message = models.TextField(max_length=512, blank=True, null=True)

    #
    # Debug information
    #
    raw_request = models.TextField(max_length=512)
    date_created = models.DateTimeField(auto_now_add=True)


    class Meta:
        #unique_together = ('trans_id', 'trans_date')
        ordering = ('-date_created',)

    def __unicode__(self):
        if self.mode == self.MODE_SUBMIT:
            return u"SUBMIT request trans_id: %s" % (self.trans_id,)
        elif self.mode == self.MODE_RETURN:
            return u"RETURN request trans_id: %s" % (self.trans_id,)
        return u"UNKNOWN request mode"

    def save(self, *args, **kwargs):
        return super(SystemPayTransaction, self).save(*args, **kwargs)

    def request(self):
        return self._as_table(self.context)
    request.allow_tags = True

    def _as_table(self, params):
        rows = []
        for k, v in sorted(params.items()):
            rows.append('<tr><th>%s</th><td>%s</td></tr>' % (k, v[0]))
        return '<table>%s</table>' % ''.join(rows)

    @property
    def context(self):
        return urlparse.parse_qs(self.raw_request, keep_blank_values=True)

    def value(self, key):
        ctx = self.context
        return ctx[key][0].decode('utf8') if key in ctx else None

    def is_complete(self):
        return not self.error_message and self.result == '00'

    @property
    def computed_signature(self):
        """
        Compute the signature on the fly
        """
        from mock import Mock
        from systempay.facade import Facade
        from django.http import QueryDict
        request = Mock()
        request.POST = QueryDict(self.raw_request)
        facade = Facade()
        form = facade.get_return_form_populated_with_request(request)
        return facade.gateway.compute_signature(form)

    @property 
    def currency(self):
        return dict(CURRENCIES).get(self.value('vads_currency'), 'UNKNOWN')

    @property
    def reference(self):
        return "%s%s" % (self.trans_date, self.trans_id)

