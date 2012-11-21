from decimal import Decimal as D
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
                order_id=order.id, 
                **kwargs
            )
        self.gateway.sign(form)
        return form

    def get_return_form_populated_with_request(self, request, **kwargs):
        """
        Prepopulate the return form with the current request
        """
        return self.gateway.get_return_form(**request.POST)

    def handle_request(self, request):
        """
        Handle the income request which can have two different forms:
            1. user coming back on the store after clicking on a "go back to store" button
            OR
            2. a notification of payment issued from SytemPay server to our server

        In both cases the data will be POST data, the only difference is that in the case 2. the 
        POST data will contain a ``hash`` parameter that needs to be include in the signature computation
        """
        form = facade.get_return_form_populated_with_request(request)

        # create the database record
        order_number = self.get_order_number(form)
        total_incl_tax = self.get_total_incl_tax(form)
        trans_record = self.record_txn(method, order_number, total_incl_tax, request)

        if not form.is_valid():
            trans_record.error_message = printable_form_errors(form)
            trans_record.save()
            raise SystemPayFormNotValid("The data received are not complete: %s. See the record #%s for more details" % (
                    printable_form_errors(form), trans_record.id)
                )

        if not facade.gateway.is_signature_valid(form):
            trans_record.error_message = u"Signature not valid. Get '%s' vs Expected '%s'" % (
                    form.cleaned_data['signature'], facade.gateway.compute_signature(form) 
                )
            trans_record.save()
            raise SystemPayFormNotValid("The data received are not valid. See the record #%s for more details" % trans_record.id)


        result = facade.get_result(form)
        if result != '00':

            if result == '02':
                raise SystemPayGatewayPaymentRejected("The shop must contact the bank")
            elif result == '05':
                raise SystemPayGatewayPaymentRejected("The payment has been rejected")
            elif result == '30':
                extra_result = facade.get_extra_result(form)
                raise SystemPayGatewayParamError(code=extra_result)
            elif result == '96':
                raise SystemPayGatewayServerError("Technical error while processing the payment")

            # TODO handle the ``auth_result`` param
            # auth_result = facade.get_auth_result(form)
            # if auth_result == '':
            #     raise SystemPayGatewayError

        return trans_record

    def record_txn(self, order_number, amount, request):
        """
        Record the transaction in the database to be able to tack everything we received
        """
        return SystemPayTransaction.objects.create(
                mode=SystemPayTransaction.MODE_RETURN,
                trans_id=request.POST.get('vads_trans_id'),
                trans_date=request.POST.get('vads_trans_date'),
                order_number=order_number,
                amount=amount,
                auth_result=request.POST.get('vads_auth_result'),
                raw_request=urlencode(request.POST)
            )
