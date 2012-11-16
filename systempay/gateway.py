from xml.dom.minidom import Document, parseString
import httplib
import re
import datetime
import logging

from oscar.apps.payment.exceptions import GatewayError

from systempay.models import SystemPayTransaction
from systempay.forms import SystemPaySubmitForm, SystemPayReturnForm

logger = logging.getLogger('systempay')


# Status codes
ACCEPTED, DECLINED, INVALID_CREDENTIALS = '1', '7', '10'


class Gateway(object):

    def __init__(self, host, context_mode, site_id, version='V1'):
        if host.startswith('http'):
            raise RuntimeError("SYSTEMPAY_HOST should not include http")
        self._host = host

        if context_mode not in ('TEST', 'PRODUCTION'):
            raise RuntimeError("Unknow context mode '%s'" % context_mode)
        self._context_mode = context_mode

        if not re.match(r'^\d{8}$', str(site_id)):
            raise RuntimeError("Config `site_id` must contain exactly 8 digits, which is wrong : '%s'" % site_id)
        self._site_id = site_id

        self._version = version

    def _values_for_submit_signature(self, data):
        return list(data.get(k, '') for k in SystemPayTransaction.PARAMS_SIGNATURE_SUBMIT_REQUEST)

    def _get_trans_date(self):
        return datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')

    def _get_trans_id(self):
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

    def get_submit_form_populated_with_basket(self, basket, **kwargs):
        """
        Prepopulate the submit form with basket data

        :basket: an oscar basket instance
        :kwargs: additional data, check the fields of the `SystemPaySubmitForm` class to see all possible values.
        """
        data = {}

        # additionnal data
        data.update(kwargs)

        # required values
        # NB: we set the required values after so that we control format of those params
        data['amount'] = int(basket.total_incl_tax * 100)  # convert into an indivisible integer
        data['capture_delay'] = kwargs.get('capture_delay', '')
        data['currency'] = kwargs.get('currency', 978)       # 978 stands for EURO (ISO 639-1)
        data['ctx_mode'] = self._context_mode
        data['payment_cards'] = kwargs.get('payment_cards', '')
        data['payment_config'] = kwargs.get('payment_config', 'SINGLE')
        data['site_id'] = self._site_id
        data['trans_date'] = self._get_trans_date()
        data['trans_id'] = self._get_trans_id()
        data['validation_mode'] = kwargs.get('validation_mode', '')
        data['version'] = self._version

        return SystemPaySubmitForm(data)

    def get_return_form_populated_with_request(self, request, **kwargs):
        """
        Prepopulate the return form with the current request
        """
        data = {}

        # additonal init data
        data.update(kwargs)

        # udpate with request data
        data.update(request.POST)

        return SystemPayReturnForm(data)
        