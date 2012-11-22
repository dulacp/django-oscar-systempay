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
    """
    Gateway to make a fine API to interface with the SystemPay gateway of Cyberplus

    The current implementation is based on the document V2 available online.
    https://systempay.cyberpluspaiement.com/html/Doc/2.2_Guide_d_implementation_formulaire_Paiement_V2.pdf
    """

    URL = "https://paiement.systempay.fr/vads-payment/"

    def __init__(self, sandbox_mode, site_id, certificate, action_mode, version='V2', notify_user_by_email=False,
            post_on_customer_return=False, custom_contracts=None):

        if sandbox_mode == False:
            context_mode = 'PRODUCTION'
        else:
            context_mode = 'TEST'
        self._context_mode = context_mode

        if not re.match(r'^\d{8}$', str(site_id)):
            raise RuntimeError("Config `site_id` must contain exactly 8 digits, and is not : '%s'" % site_id)
        self._site_id = site_id

        if action_mode not in ('INTERACTIVE', 'SILENT'):
            raise RuntimeError("Config `action_mode`='%s' is not supported by the current version" % action_mode)
        self._action_mode = action_mode

        self._certificate = certificate
        self._version = version

        # optional params (impact the required params)
        self._notify_user_by_email = notify_user_by_email
        self._post_on_customer_return = post_on_customer_return
        self._custom_contracts = custom_contracts

    def compute_signature(self, form):
        """
        Compute the signature according to the doc
        """
        
        params = form.values_for_signature(form.data)
        sign = '+'.join(params) + '+' + self._certificate
        print "sign", sign
        return sha1(sign).hexdigest()

    def is_signature_valid(self, form):
        if form.is_valid():
            signature = self.compute_signature(form)
            return signature == form.cleaned_data['signature']

    def sign(self, form):
        form.data['signature'] = self.compute_signature(form)

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
        data['vads_action_mode'] = self._action_mode 
        data['vads_amount'] = self.format_amount(amount)
        data['vads_currency'] = kwargs.get('vads_currency', '978')     # 978 stands for EURO (ISO 639-1)
        data['vads_ctx_mode'] = self._context_mode
        data['vads_page_action'] = 'PAYMENT'
        data['vads_payment_config'] = kwargs.get('vads_payment_config', 'SINGLE')
        data['vads_site_id'] = self._site_id
        data['vads_trans_date'] = self.get_trans_date()
        data['vads_trans_id'] = self.get_trans_id()
        data['vads_validation_mode'] = kwargs.get('vads_validation_mode', '')
        data['vads_version'] = self._version

        # requirement depends on the configuration
        if self._notify_user_by_email:
            data['vads_cust_email'] = kwargs.get('user_email', '') 

        # TODO implement those potential settings
        # if self._post_on_customer_return
        #     data['vads_return_mode'] = kwargs.get('')

        if self._custom_contracts:
            data['vads_contracts'] = self._custom_contracts


        # optional parameters
        data['vads_return_mode'] = 'GET'

        return SystemPaySubmitForm(data)

    def get_return_form(self, **kwargs):
        """
        Prepopulate the return form with the current request
        """
        data = {}
        data.update(kwargs) # additonal init data
        return SystemPayReturnForm(data)
        