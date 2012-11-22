from decimal import Decimal as D
from urllib import urlencode
import logging

from django.conf import settings
from django.db.models import get_model

from systempay import gateway
from systempay.models import SystemPayTransaction
from systempay.forms import SystemPaySubmitForm, SystemPayReturnForm
from systempay.exceptions import *

logger = logging.getLogger('systempay')

SystemPayTransaction = get_model('systempay', 'SystemPayTransaction')


class Facade(object):
    """
    A bridge between oscar's objects and the core gateway object
    """

    def __init__(self):
        self.gateway = gateway.Gateway(settings.SYSTEMPAY_SANDBOX_MODE,
                                       settings.SYSTEMPAY_SITE_ID, 
                                       settings.SYSTEMPAY_CERTIFICATE,
                                       getattr(settings, 'SYSTEMPAY_ACTION_MODE', 'INTERACTIVE'),
                                      )
        self.currency = getattr(settings, 'SYSTEMPAY_CURRENCY', 978) # 978 stands for EURO (ISO 639-1)

    def get_order_number(self, form):
        return form.data.get('vads_order_id')

    def get_total_incl_tax(self, form):
        return D(int(form.data.get('vads_amount'))/100.0)

    def get_result(self, form):
        return form.data.get('vads_result')

    def get_extra_result(self, form):
        return form.data.get('vads_extra_result')

    def get_auth_result(self, form):
        return form.data.get('vads_auth_result')

    def get_submit_form_populated_with_order(self, order, **kwargs):
        """
        Prepopulate the submit form with order data

        :order: an oscar order instance
        :kwargs: additional data, check the fields of the `SystemPaySubmitForm` class to see all possible values.
        """
        form = self.gateway.get_submit_form(
                order.total_incl_tax, 
                vads_order_id=order.number, 
                **kwargs
            )
        self.gateway.sign(form)
        return form

    def get_return_form_populated_with_request(self, request, **kwargs):
        """
        Prepopulate the return form with the current request
        """
        return self.gateway.get_return_form( **dict( (k, request.POST.get(k)) for k in request.POST ) )

    def handle_request(self, request):
        """
        Handle the income request which can have two different forms:
            1. user coming back on the store after clicking on a "go back to store" button
            OR
            2. a notification of payment issued from SytemPay server to our server

        In both cases the data will be POST data, the only difference is that in the case 2. the 
        POST data will contain a ``hash`` parameter that needs to be include in the signature computation
        """
        form = self.get_return_form_populated_with_request(request)

        # create the database record
        order_number = self.get_order_number(form)
        total_incl_tax = self.get_total_incl_tax(form)
        txn = self.record_return_txn(order_number, total_incl_tax, request)

        if not form.is_valid():
            txn.error_message = printable_form_errors(form)
            txn.save()
            raise SystemPayFormNotValid("The data received are not complete: %s. See the transaction record #%s for more details" % (
                    printable_form_errors(form), txn.id)
                )

        if not self.gateway.is_signature_valid(form):
            txn.error_message = u"Signature not valid. Get '%s' vs Expected '%s'" % (
                    form.cleaned_data['signature'], self.gateway.compute_signature(form) 
                )
            txn.save()
            raise SystemPayFormNotValid("The data received are not valid. See the transaction record #%s for more details" % txn.id)

        if not txn.is_complete():

            if txn.result == '02':
                raise SystemPayGatewayPaymentRejected("The shop must contact the bank")
            elif txn.result == '05':
                raise SystemPayGatewayPaymentRejected("The payment has been rejected")
            elif txn.result == '30':
                extra_result = self.get_extra_result(form)
                raise SystemPayGatewayParamError(code=extra_result)
            elif txn.result == '96':
                raise SystemPayGatewayServerError("Technical error while processing the payment")
            else:
                raise SystemPayGatewayServerError("Unknown error")

            # TODO handle the ``auth_result`` param
            # auth_result = self.get_auth_result(form)
            # if auth_result == '':
            #     raise SystemPayGatewayError

        return txn

    def record_submit_txn(self, order_number, amount, form):
        return self.record_txn(order_number, amount, form.data, SystemPayTransaction.MODE_SUBMIT)

    def record_return_txn(self, order_number, amount, request):
        """
        Record the transaction in the database to be able to tack everything we received
        """
        return self.record_txn(order_number, amount, request.POST, SystemPayTransaction.MODE_RETURN)

    def record_txn(self, order_number, amount, data, mode):
        """
        Record the transaction in the database to be able to tack everything we received
        """
        return SystemPayTransaction.objects.create(
                mode=mode,
                operation_type=data.get('vads_operation_type'),
                trans_id=data.get('vads_trans_id'),
                trans_date=data.get('vads_trans_date'),
                order_number=order_number,
                amount=amount,
                auth_result=data.get('vads_auth_result'),
                result=data.get('vads_result'),
                raw_request=urlencode(data)
            )
