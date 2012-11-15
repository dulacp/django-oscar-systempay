import urlparse
from hashlib import sha1

from django.db import models


class ResponseModel(models.Model):

    # Mode (send or return) request
    MODE_SEND, MODE_RETURN = ('send', 'return')
    MODE_CHOICES = (
            (MODE_SEND, u"Send"),
            (MODE_RETURN, u"Return"),
        )
    mode = models.CharField(choices=MODE_CHOICES)

    # Transaction details used by both SystemPay SEND and RETURN request
    amount = models.IntegerField(max_digits=12, decimal_places=2, blank=True) # NB: expressed in cents for euros (unity undivisible)
    capture_delay = models.IntegerField(max_digits=3, blank=True)
    currency = models.IntegerField(min_digits=3, max_digits=3, blank=True) # ISO 4217

    CONTEXT_TEST, CONTEXT_PRODUCTION = ('TEST', 'PRODUCTION')
    CONTEXT_CHOICES = (
            (CONTEXT_TEST, u"TEST"),
            (CONTEXT_PRODUCTION, u"PRODUCTION")
        )
    ctx_mode = models.CharField(choices=CONTEXT_CHOICES)

    # needs to be formated as SINGLE or MULTI:first=val1;count=val2;period=val3
    # example: MULTI:first=5000;count=3;period=30 
    #          would represent a payment segmented with a first account of 50,00
    #          then the rest of the amount would be divided in (count-1) other payments
    #          with a timelapse of 30 days between them
    #
    # NB: if the validity date of the credit card can't handle the last payment (in case of multi)
    #     the whole transaction will be rejected
    payment_config = models.CharField(max_length=127, blank=True)

    PAYMENT_SOURCE_EMPTY, PAYMENT_SOURCE_BO, PAYMENT_SOURCE_MOTO, PAYMENT_SOURCE_CC, PAYMENT_SOURCE_OTHER = (
        '', 'BO', 'MOTO', 'CC', 'OTHER')
    PAYMENT_SOURCE_CHOICES = (
            (PAYMENT_SOURCE_EMPTY, u""),
            (PAYMENT_SOURCE_BO, u"BO"),
            (PAYMENT_SOURCE_MOTO, u"MOTO"),
            (PAYMENT_SOURCE_CC, u"CC"),
            (PAYMENT_SOURCE_OTHER, u"OTHER"),
        )
    payment_src = models.CharField(max_length=5, blank=True, default=";")

    signature = models.CharField(min_length=40, max_length=40, blank=True)
    site_id = models.IntegerField(max_digits=8, blank=True)

    # Need to respect the format ``YYYYMMDDHHMMSS`` in UTC timezone
    trans_date = models.IntegerField(max_digits=14, blank=True)

    # Unique identifier in the range 000000 to 899999. Integer between 900000 and 999999 are reserved
    # NB: it should only be unique over the current day
    trans_id = models.IntegerField(max_length=6, blank=True)
    validation_mode = models.IntegerField(max_digits=1, blank=True, default="")
    version = models.CharField(max_length=10, blank=True)

    order_id = models.CharField(max_length=32, null=True, blank=True)
    order_info = models.CharField(max_length=255, null=True, blank=True)
    order_info2 = models.CharField(max_length=255, null=True, blank=True)
    order_info3 = models.CharField(max_length=255, null=True, blank=True)

    cust_address = models.CharField(max_length=255, null=True, blank=True)
    cust_country = models.CharField(min_length=2, max_length=2, null=True, blank=True)
    cust_email = models.CharField(max_length=127, null=True, blank=True)
    cust_id = models.CharField(max_length=63, null=True, blank=True)
    cust_name = models.CharField(max_length=127, null=True, blank=True)
    cust_phone = models.CharField(max_length=63, null=True, blank=True)
    cust_title = models.CharField(max_length=63, null=True, blank=True)
    cust_city = models.CharField(max_length=63, null=True, blank=True)
    cust_zip = models.CharField(max_length=63, null=True, blank=True)

    language = models.CharField(min_length=2, max_length=2, null=True, blank=True)
    user_info = models.CharField(max_length=255, null=True, blank=True)

    # Can be used to customize the aspect of the transaction page
    theme_config = models.CharField(max_length=255, null=True, blank=True)

    #
    # Debug information
    #
    raw_request = models.TextField(max_length=512)
    raw_response = models.TextField(max_length=512)

    response_time = models.FloatField(help_text="Response time in milliseconds")

    date_created = models.DateTimeField(auto_now_add=True)


    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        return super(ExpressTransaction, self).save(*args, **kwargs)

    def request(self):
        request_params = urlparse.parse_qs(self.raw_request)
        return self._as_table(request_params)
    request.allow_tags = True

    def response(self):
        return self._as_table(self.context)
    response.allow_tags = True

    def _as_table(self, params):
        rows = []
        for k, v in sorted(params.items()):
            rows.append('<tr><th>%s</th><td>%s</td></tr>' % (k, v[0]))
        return '<table>%s</table>' % ''.join(rows)

    @property
    def context(self):
        return urlparse.parse_qs(self.raw_response)

    def value(self, key):
        ctx = self.context
        return ctx[key][0].decode('utf8') if key in ctx else None

    def _compute_signature(self, params):
        """
        Compute the signature according to the doc
        """
        sign = '+'.join(params) + '+' + getattr(settings, 'SYSTEMPAY_CERTIFICATE', '')
        return sha1(sign).hexdigest()

    @property
    def signature_params(self):
        raise NotImplementedError, u"Need to implement this method in subclass"

    def compute_signature(self):
        return self._compute_signature([getattr(self, param) for param in self.send_signature_params])

    def is_signature_valid(self):
        return self.compute_signature() == self.signature


class SystemPaySendRequest(ResponseModel):

    contrib = models.CharField(max_length=255, null=True, blank=True)

    payment_cards = models.CharField(max_length=127, blank=True, default="")

    url_success = models.CharField(max_length=127, null=True, blank=True)
    url_referral = models.CharField(max_length=127, null=True, blank=True)
    url_refused = models.CharField(max_length=127, null=True, blank=True)
    url_cancel = models.CharField(max_length=127, null=True, blank=True)
    url_error = models.CharField(max_length=127, null=True, blank=True)
    url_return = models.CharField(max_length=127, null=True, blank=True)

    contracts = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        ordering = ('-date_created',)

    def __unicode__(self):
        return u"Send request trans_id: %s" % (self.trans_id,)

    @property
    def signature_params(self):
        return (
                'version', 
                'site_id', 
                'ctx_mode', 
                'trans_id', 
                'trans_date', 
                'validation_mode', 
                'capture_delay', 
                'payment_config', 
                'payment_cards', 
                'amount', 
                'currency',
            )


class SystemPayReturnRequest(ResponseModel):

    auth_result = models.IntegerField(min_digits=2, max_digits=2, blank=True)

    AUTH_MODE_MARK, AUTH_MODE_FULL = ('MARK', 'FULL')
    AUTH_MODE_CHOICES = (
            (AUTH_MODE_MARK, u"MARK"),
            (AUTH_MODE_FULL, u"FULL")
        )
    auth_mode = models.CharField(choices=AUTH_MODE_CHOICES, blank=True)
    auth_number = models.IntegerField(min_digits=6, max_digits=6, blank=True)

    card_brand = models.CharField(max_length=127, blank=True)
    card_number = models.CharField(max_length=19, blank=True)

    extra_result = models.IntegerField(min_digits=2, max_digits=2, blank=True)

    WARRANTY_RESULT_EMPTY, WARRANTY_RESULT_YES, WARRANTY_RESULT_NO, WARRANTY_RESULT_UNKNOWN = (
            '', 'YES', 'NO', 'UNKNOWN'
        )
    WARRANTY_RESULT_CHOICES = (
            (WARRANTY_RESULT_EMPTY, u""),
            (WARRANTY_RESULT_YES, u"YES"),
            (WARRANTY_RESULT_NO, u"NO"),
            (WARRANTY_RESULT_UNKNOWN, u"UNKNOWN"),
        )
    warranty_result = models.CharField(choices=WARRANTY_RESULT_CHOICES)
    payment_certificate = models.CharField(min_length=40, max_length=40, blank=True)
    result = models.IntegerField(min_digits=2, max_digits=2)

    class Meta:
        ordering = ('-date_created',)

    def __unicode__(self):
        return u"Return request trans_id: %s" % (self.trans_id,)

    @property
    def signature_params(self):
        return (
                'version',
                'site_id',
                'ctx_mode',
                'trans_id',
                'trans_date',
                'validation_mode',
                'capture_delay',
                'payment_config',
                'card_brand',
                'card_number',
                'amount',
                'currency',
                'auth_mode',
                'auth_result',
                'auth_number',
                'warranty_result',
                'payment_certificate',
                'result',
            )
