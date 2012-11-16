import urlparse

from django.db import models


class SystemPayTransaction(models.Model):

    # Mode (send or return) request
    MODE_SUBMIT, MODE_RETURN = ('Submit', 'Return')
    MODE_CHOICES = (
            (MODE_SUBMIT, u"Submit Request"),
            (MODE_RETURN, u"Return Request"),
        )
    mode = models.CharField(max_length=10, choices=MODE_CHOICES)

    # Unique identifier in the range 000000 to 899999. Integer between 900000 and 999999 are reserved
    # NB: it should only be unique over the current day
    trans_id = models.CharField(max_length=6, blank=True)

    # Need to respect the format ``YYYYMMDDHHMMSS`` in UTC timezone
    trans_date = models.CharField(max_length=14, blank=True)

    auth_result = models.CharField(max_length=2, blank=True)
    return_code = models.CharField(max_length=2, blank=True)

    error_code = models.CharField(max_length=32, null=True, blank=True)
    error_message = models.CharField(max_length=256, null=True, blank=True)

    #
    # Debug information
    #
    raw_request = models.TextField(max_length=512)
    response_time = models.FloatField(help_text="Response time in milliseconds")
    date_created = models.DateTimeField(auto_now_add=True)


    class Meta:
        unique_together = ('trans_id', 'trans_date')
        ordering = ('-date_created',)

    def __unicode__(self):
        if self.mode == self.MODE_SUBMIT:
            return u"SUBMIT request trans_id: %s" % (self.trans_id,)
        elif self.mode == self.MODE_RETURN:
            return u"RETURN request trans_id: %s" % (self.trans_id,)
        return u"UNKNOWN request mode"

    def save(self, *args, **kwargs):
        return super(ExpressTransaction, self).save(*args, **kwargs)

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
        return urlparse.parse_qs(self.raw_request)

    def value(self, key):
        ctx = self.context
        return ctx[key][0].decode('utf8') if key in ctx else None
