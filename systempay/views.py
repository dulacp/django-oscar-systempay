# encoding: utf-8

from decimal import Decimal as D
from urllib import urlencode
import logging

from django.db.models import get_model
from django.views import generic
from django.http import Http404, HttpResponseRedirect, HttpResponseBadRequest
from django.core.urlresolvers import reverse

from oscar.apps.checkout.views import PaymentDetailsView, CheckoutSessionMixin

from systempay.facade import Facade
from systempay.exceptions import *

logger = logging.getLogger('systempay')

Order = get_model('order', 'Order')
Source = get_model('payment', 'Source')
SourceType = get_model('payment', 'SourceType')


def printable_form_errors(form):
        return u' / '.join([u"%s: %s" % (f.name, '. '.join(f.errors)) for f in form])


class SecureRedirectView(generic.DetailView):
    template_name = 'systempay/secure_redirect.html'
    context_object_name = 'order'

    _order = None

    def get_object(self):
        if self._order is not None:
            return self._order

        # We allow superusers to force an order thankyou page for testing
        order = None
        if self.request.user.is_superuser:
            if 'order_number' in self.request.GET:
                order = Order._default_manager.get(number=self.request.GET['order_number'])
            elif 'order_id' in self.request.GET:
                order = Order._default_manager.get(id=self.request.GET['orderid'])

        if not order:
            if 'checkout_order_id' in self.request.session:
                order = Order._default_manager.get(pk=self.request.session['checkout_order_id'])
            else:
                raise Http404(_("No order found"))

        self._order = order
        return order

    def get_context_data(self, **kwargs):
        ctx = super(SecureRedirectView, self).get_context_data(**kwargs)
        order = self.get_object()
        ctx['submit_form'] = Facade().get_submit_form_populated_with_order(order)
        return ctx


class CancelResponseView(generic.RedirectView):
    def get_redirect_url(self, **kwargs):
        messages.error(self.request, u"La transaction System Pay a été annulée")
        return reverse('basket:summary')


class PlaceOrderView(PaymentDetailsView):
    template_name = 'systempay/preview.html'
    template_name_preview = 'systempay/preview.html'
    preview = True

    def post(self, request, *args, **kwargs):
        error_response = self.get_error_response()

        if error_response:
            return error_response
        if self.preview:
            # We use a custom parameter to indicate if this is an attempt to place an order.
            # Without this, we assume a payment form is being submitted from the
            # payment-details page
            if request.POST.get('action', '') == 'place_order':
                return self.submit(request.basket, payment_kwargs={'currency': "EUR"})
            return self.render_preview(request)

        # Posting to payment-details isn't the right thing to do
        return self.get(request, *args, **kwargs)

    def handle_payment(self, order_number, total_incl_tax, **kwargs):
        """
        Skip this step when placing the order, it'll be handle by the ipn received from server to server.
        Only record the allocated amount.
        """
        # Record payment source
        source_type, is_created = SourceType.objects.get_or_create(code='systempay')
        source = Source(source_type=source_type,
                        currency=kwargs.get('currency'),
                        amount_allocated=total_incl_tax,
                        amount_debited=D(0))
        self.add_payment_source(source)

    def handle_successful_order(self, order, send_confirmation_message=True):
        """
        Handle the various steps required after an order has been successfully placed.

        Override this view if you want to perform custom actions when an
        order is submitted.
        """
        # Send confirmation message (normally an email)
        # if send_confirmation_message:
        #     self.send_confirmation_message(order)

        # Flush all session data
        self.checkout_session.flush()

        # Save order id in session so secure redirect page can load it
        self.request.session['checkout_order_id'] = order.id

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('systempay:secure-redirect')


class HandleIPN(PaymentDetailsView):

    def post(self, request, *args, **kwargs):
        self.handle_ipn(request)

    def handle_ipn(self, request, **kwargs):
        """
        Complete payment with PayPal - this calls the 'DoExpressCheckout'
        method to capture the money from the initial transaction.
        """
        try: 
            txn = Facade().handle_request(request)
        except SystemPayFormNotValid, inst:
            logger.error(inst.message)
            raise UnableToTakePayment(inst.message)
        except SystemPayGatewayParamError, inst:
            logger.error(inst.message)
            raise UnableToTakePayment(inst.message)
        except SystemPayGatewayAuthorizationError, inst:
            logger.error(inst.message)
            raise PaymentError(inst.message)
        except SystemPayGatewayPaymentRejected, inst:
            logger.error(inst.message)
            raise PaymentError(inst.message)
        except SystemPayGatewayServerError, inst:
            logger.error(inst.message)
            raise UnableToTakePayment(inst.message)

        try:
            order = Order.objects.get(number=txn.order_number)
        except Order.DoesNotExist, inst:
            raise PaymentError("Unable to retrieve Order #%s" % txn.order_number)

        # Record payment source
        source_type, is_created = SourceType.objects.get_or_create(code='systempay')
        source = Source(source_type=source_type,
                        currency=txn.currency,
                        amount_allocated=D(0),
                        amount_debited=txn.amount,
                        order=order)
        source.save()
