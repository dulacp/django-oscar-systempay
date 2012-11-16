import httplib
import re
import datetime
import logging
from hashlib import sha1

from oscar.apps.payment.exceptions import GatewayError

from systempay.models import SystemPayTransaction
from systempay.forms import SystemPaySubmitForm, SystemPayReturnForm
from systempay.exceptions import *

logger = logging.getLogger('systempay')


class Gateway(object):

    def __init__(self, sandbox_mode, site_id, certificate, version='V1'):
        if sandbox_mode == False:
            context_mode = 'PRODUCTION'
        else:
            context_mode = 'TEST'
        self._context_mode = context_mode

        if not re.match(r'^\d{8}$', str(site_id)):
            raise RuntimeError("Config `site_id` must contain exactly 8 digits, which is wrong : '%s'" % site_id)
        self._site_id = site_id

        self._certificate = certificate
        self._version = version
        self._url = "https://paiement.systempay.fr/vads-payment/"

    def compute_signature(self, form):
        """
        Compute the signature according to the doc
        """
        if form.is_valid():
            params = form.values_for_signature(form.cleaned_data)
            sign = '+'.join(params) + '+' + self._certificate
            return sha1(sign).hexdigest()
        raise SystemPayFormNotValid, u"signature can't be computed because the form is not valid '%s'" % form.errors

    def is_signature_valid(self, form):
        if form.is_valid():
            signature = self.compute_signature(form)
            return signature == form.cleaned_data['signature']

    def sign(self, form):
        if form.is_valid():
            form.cleaned_data['signature'] = self.compute_signature(form)
            return True 
        return False

    def format_amount(self, amount):
        """
        Format the amount to respond to the plateform needs, which is a undivisible version of the amount.

        c.g. if amount = $50.24 
             then format_amount = 5024
        """
        return int(amount * 100)

    def get_trans_date(self):
        return datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')

    def get_trans_id(self):
        """
        Range allowed is between 000000 and 899999.
        So if we assume that there is only one transaction per seconde, that covers 86400 
        unique transactions.
        And to decrease the probability of a collision between two customers at the same second
        we can use the first digit of the microsecond.

        It's not completely bulletproof because it can happen if two person confirm their order 
        at the same time, same second and the same microsecond.
        """
        n = datetime.datetime.utcnow()
        return "%06d" % (n.hour*36000 + n.minute*600 + n.second*10 + n.microsecond/10000)

    def get_submit_form(self, amount, **kwargs):
        """
        Prepopulate the submit form with the data

        :amount: decimal or float amount value of the order
        :kwargs: additional data, check the fields of the `SystemPaySubmitForm` class to see all possible values.
        """
        data = {}
        data.update(kwargs) # additionnal data

        # required values
        # NB: we set the required values after so that we control format of those params
        data['amount'] = self.format_amount(amount)
        data['capture_delay'] = kwargs.get('capture_delay', '')
        data['currency'] = kwargs.get('currency', 978)     # 978 stands for EURO (ISO 639-1)
        data['ctx_mode'] = self._context_mode
        data['payment_cards'] = kwargs.get('payment_cards', '')
        data['payment_config'] = kwargs.get('payment_config', 'SINGLE')
        data['site_id'] = self._site_id
        data['trans_date'] = self.get_trans_date()
        data['trans_id'] = self.get_trans_id()
        data['validation_mode'] = kwargs.get('validation_mode', '')
        data['version'] = self._version

        return SystemPaySubmitForm(data)

    def get_return_form(self, **kwargs):
        """
        Prepopulate the return form with the current request
        """
        data = {}
        data.update(kwargs) # additonal init data
        return SystemPayReturnForm(data)
        