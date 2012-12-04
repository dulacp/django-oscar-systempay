# encoding: utf-8

from decimal import Decimal as D
import logging

from django.conf import settings
from django.db.models import get_model
from django.views import generic
from django.contrib import messages
from django.http import HttpResponse, Http404, HttpResponseRedirect, HttpResponseBadRequest
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from oscar.core.loading import get_class, get_classes

from systempay.models import SystemPayTransaction
from systempay.facade import Facade
from systempay.exceptions import *

logger = logging.getLogger('systempay')

Basket = get_model('basket', 'Basket')
Order = get_model('order', 'Order')
Source = get_model('payment', 'Source')
SourceType = get_model('payment', 'SourceType')

PaymentDetailsView, CheckoutSessionMixin = get_classes('checkout.views', ['PaymentDetailsView', 'CheckoutSessionMixin'])
PaymentError, UnableToTakePayment = get_classes('payment.exceptions', ['PaymentError', 'UnableToTakePayment'])

EventHandler = get_class('order.processing', 'EventHandler')


def printable_form_errors(form):
        return u' / '.join([u"%s: %s" % (f.name, '. '.join(f.errors)) for f in form])


class SecureRedirectView(CheckoutSessionMixin, generic.DetailView):
    template_name = 'systempay/secure_redirect.html'
    context_object_name = 'order'

    _order = None
    _form = None

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

    def get_form(self):
        if self._form is not None:
            return self._form
        order = self.get_object()
        self._form = Facade().get_submit_form_populated_with_order(order)
        return self._form

    def get(self, *args, **kwargs):
        # record the request
        order = self.get_object()
        form = self.get_form()
        Facade().record_submit_txn(order.number, order.total_incl_tax, form)
        response = super(SecureRedirectView, self).get(*args, **kwargs)

        # Flush of all session data
        self.checkout_session.flush()

        return response

    def get_context_data(self, **kwargs):
        ctx = super(SecureRedirectView, self).get_context_data(**kwargs)
        ctx['submit_form'] = self.get_form()
        return ctx


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
        payment_method = self.checkout_session.payment_method()
        if payment_method is None:
            messages.error(self.request, _("Please choose a payment method."))
            return HttpResponseRedirect(reverse('checkout:payment-method'))

        source_type, is_created = SourceType.objects.get_or_create(code=payment_method)
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

        # Delay the flush of all session data
        # self.checkout_session.flush()

        # Save order id in session so secure redirect page can load it
        self.request.session['checkout_order_id'] = order.id

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('systempay:secure-redirect')


class ResponseView(generic.RedirectView):
    def get_order(self):
        # We allow superusers to force an order thankyou page for testing
        order = None
        if self.request.user.is_superuser:
            if 'order_number' in self.request.GET:
                order = Order._default_manager.get(number=self.request.GET['order_number'])
            elif 'order_id' in self.request.GET:
                order = Order._default_manager.get(id=self.request.GET['orderid'])

        if not order:
            order_number = None
            if 'vads_order_id' in self.request.POST:
                order_number = self.request.POST['vads_order_id']
            elif 'vads_order_id' in self.request.GET:
                order_number = self.request.GET['vads_order_id']

            if not order_number:
                raise Http404(_("No order found"))

            try:
                order = Order._default_manager.get(number=order_number)
            except Order.DoesNotExist:
                raise Http404(_("The page requested seems outdated"))

        return order


class ReturnResponseView(ResponseView):
    def get_redirect_url(self, **kwargs):
        order = self.get_order()

        # check if the transaction exists
        txns = SystemPayTransaction.objects.filter(
                mode=SystemPayTransaction.MODE_RETURN, 
                order_number=order.number
            ).order_by('-date_created')[:1]

        if not txns:
            messages.error(self.request, _("No response received from your bank for the moment. "
                                       "Be patient, we'll get back to you as soon as we receive it.") )
        else:
            txn = txns[0]
            if txn.is_complete(): # check if the transaction has been complete
                messages.success(self.request, _("Your payment has been successfully validated."))
            else:
                messages.error(self.request, _("Your payment has been rejected for the reason. You will not be charged. Contact the support for more details."))

        self.request.session['checkout_order_id'] = order.id
        return reverse('checkout:thank-you')


class CancelResponseView(ResponseView):
    def get_redirect_url(self, **kwargs):
        order = self.get_order()

        # cancel the order (to deallocate the products)
        handler = EventHandler()
        handler.handle_order_status_change(order, getattr(settings, 'OSCAR_STATUS_CANCELLED', None))

        # delete the order
        order.delete()

        # unfreeze the basket
        basket = Basket.objects.get(pk=order.basket_id)
        basket.thaw()

        messages.error(self.request, _("The transaction has be canceled"))
        return reverse('basket:summary')


class HandleIPN(generic.View):

    def get(self, request, *args, **kwargs):
        if request.user and request.user.is_superuser:
            # Authorize admins for test purpose to copy the GET params to the POST dict
            request.POST = request.GET
            return self.post(request, *args, **kwargs)
        return HttpResponse()

    def post(self, request, *args, **kwargs):
        try:
            self.handle_ipn(request)
        except PaymentError, inst:
            return HttpResponseBadRequest(inst.message)
        return HttpResponse()

    def handle_ipn(self, request, **kwargs):
        """
        Complete payment with PayPal - this calls the 'DoExpressCheckout'
        method to capture the money from the initial transaction.
        """
        txn = None
        try:
            txn = Facade().handle_request(request)
            order = Order.objects.get(number=txn.order_number)

            # Record payment source
            source_type, is_created = SourceType.objects.get_or_create(code='systempay')

            if txn.operation_type == SystemPayTransaction.OPERATION_TYPE_DEBIT:
                source = Source(source_type=source_type,
                                currency=txn.currency,
                                amount_allocated=D(0),
                                amount_debited=txn.amount,
                                order=order)
                source.save()
            elif txn.operation_type == SystemPayTransaction.OPERATION_TYPE_CREDIT:
                source = Source(source_type=source_type,
                                currency=txn.currency,
                                amount_allocated=D(0),
                                amount_refunded=txn.amount,
                                order=order)
                source.save()
            else:
                raise PaymentError(_("Unknown operation type '%(operation_type)s'") % {'operation_type': txn.operation_type})

        except SystemPayError, inst:
            logger.error(inst.message)
            #raise PaymentError(inst.message)
        except Order.DoesNotExist, inst:
            logger.error(_("Unable to retrieve Order #%(order_number)s") % {'order_number': txn.order_number})
            #raise PaymentError(_("Unable to retrieve Order #%(order_number)s") % {'order_number': txn.order_number})
