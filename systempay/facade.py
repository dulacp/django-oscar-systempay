import logging

from django.conf import settings

from systempay import gateway
from systempay.models import SystemPayTransaction
from systempay.forms import SystemPaySubmitForm, SystemPayReturnForm

logger = logging.getLogger('systempay')


class Facade(object):
    """
    A bridge between oscar's objects and the core gateway object
    """

    def __init__(self):
        self.gateway = gateway.Gateway(settings.SYSTEMPAY_SANDBOX_MODE,
                                       settings.SYSTEMPAY_SITE_ID, 
                                       settings.SYSTEMPAY_CERTIFICATE,
                                      )
        self.currency = getattr(settings, 'SYSTEMPAY_CURRENCY', 978) # 978 stands for EURO (ISO 639-1)

    def get_submit_form_populated_with_order(self, order, **kwargs):
        """
        Prepopulate the submit form with order data

        :order: an oscar order instance
        :kwargs: additional data, check the fields of the `SystemPaySubmitForm` class to see all possible values.
        """
        return self.gateway.get_submit_form(
                order.total_incl_tax, 
                order_id=order.id, 
                **kwargs
            )

    def get_return_form_populated_with_request(self, request, **kwargs):
        """
        Prepopulate the return form with the current request
        """
        return self.gateway.get_return_form(**request.POST)

    def handle_request(self, order_number, amount, request):
        """
        Handle the income request which can have two different forms:
            1. user coming back on the store after clicking on a "go back to store" button
            OR
            2. a notification of payment issued from SytemPay server to our server

        In both cases the data will be POST data, the only difference is that in the case 2. the 
        POST data will contain a ``hash`` parameter that needs to be include in the signature computation
        """
        self.record_txn(method, order_number, amount, response)

    def record_txn(self, order_number, amount, request):
        """
        Record the transaction in the databse to be able to tack everything we received
        """
        SystemPayTransaction.objects.create(
                order_number=order_number
            )
