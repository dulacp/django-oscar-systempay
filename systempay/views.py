from django.template import generic

class SecureRedirectView(generic.TemplateView)
    template_name = 'systempay/secure_redirect.html'


class CancelResponseView(RedirectView):
    def get_redirect_url(self, **kwargs):
        messages.error(self.request, "PayPal transaction cancelled")
        return reverse('basket:summary')


class SuccessResponseView(PaymentDetailsView):
    template_name_preview = 'systempay/preview.html'
    preview = True

    def get(self, request, *args, **kwargs):
        """
        Fetch details about the successful transaction from
        PayPal.  We use these details to show a preview of
        the order with a 'submit' button to place it.
        """
        try:
            payer_id = request.GET['PayerID']
            token = request.GET['token']
        except KeyError:
            # Manipulation - redirect to basket page with warning message
            messages.error(self.request, "Unable to determine PayPal transaction details")
            return HttpResponseRedirect(reverse('basket:summary'))

        try:
            self.fetch_paypal_data(payer_id, token)
        except PayPalError:
            messages.error(self.request, "A problem occurred communicating with PayPal - please try again later")
            return HttpResponseRedirect(reverse('basket:summary'))
        return super(SuccessResponseView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        Place an order.

        We fetch the txn details again and then proceed with oscar's standard
        payment details view for placing the order.
        """
        try:
            payer_id = request.POST['payer_id']
            token = request.POST['token']
        except KeyError:
            # Probably suspicious manipulation if we get here
            messages.error(self.request, "A problem occurred communicating with PayPal - please try again later")
            return HttpResponseRedirect(reverse('basket:summary'))
        try:
            self.fetch_paypal_data(payer_id, token)
        except PayPalError:
            # Unable to fetch txn details from PayPal - we have to bail out
            messages.error(self.request, "A problem occurred communicating with PayPal - please try again later")
            return HttpResponseRedirect(reverse('basket:summary'))

        # Pass the user email so it can be stored with the order
        order_kwargs = {'guest_email': self.txn.value('EMAIL')}

        return self.submit(request.basket, order_kwargs=order_kwargs)

    def fetch_paypal_data(self, payer_id, token):
        self.payer_id = payer_id
        self.token = token
        self.txn = fetch_transaction_details(token)

    def get_error_response(self):
        # We bypass the normal session checks for shipping address and shipping
        # method as they don't apply here.
        pass

    def get_context_data(self, **kwargs):
        ctx = super(SuccessResponseView, self).get_context_data(**kwargs)
        if not hasattr(self, 'payer_id'):
            return ctx
        ctx.update({
            'payer_id': self.payer_id,
            'token': self.token,
            'paypal_user_email': self.txn.value('EMAIL'),
            'paypal_amount': D(self.txn.value('AMT')),
        })
        # We convert the PayPal response values into those that match Oscar's normal
        # context so we can re-use the preview template as is
        shipping_address_fields = [
            self.txn.value('PAYMENTREQUEST_0_SHIPTONAME'),
            self.txn.value('PAYMENTREQUEST_0_SHIPTOSTREET'),
            self.txn.value('PAYMENTREQUEST_0_SHIPTOCITY'),
            self.txn.value('PAYMENTREQUEST_0_SHIPTOSTATE'),
            self.txn.value('PAYMENTREQUEST_0_SHIPTOZIP'),
            self.txn.value('PAYMENTREQUEST_0_SHIPTOCOUNTRYNAME'),
        ]
        ctx['shipping_address'] = {
            'active_address_fields': filter(bool, shipping_address_fields),
            'notes': self.txn.value('NOTETEXT'),
        }
        shipping_method = self.get_shipping_method()
        if shipping_method:
            ctx['shipping_method'] = shipping_method
        else:    
            ctx['shipping_method'] = {
                'name': self.txn.value('SHIPPINGOPTIONNAME'),
                'description': '',
                'basket_charge_incl_tax': D(self.txn.value('SHIPPINGAMT')),
            }
        ctx['order_total_incl_tax'] = D(self.txn.value('PAYMENTREQUEST_0_AMT'))
        return ctx

    def handle_payment(self, order_number, total_incl_tax, **kwargs):
        """
        Complete payment with PayPal - this calls the 'DoExpressCheckout'
        method to capture the money from the initial transaction.
        """
        try:
            payer_id = self.request.POST['payer_id']
            token = self.request.POST['token']
        except KeyError:
            raise PaymentError("Unable to determine PayPal transaction details")

        try:
            txn = confirm_transaction(payer_id, token, amount=self.txn.amount,
                                      currency=self.txn.currency)
        except PayPalError:
            raise UnableToTakePayment()

        # Record payment source
        source_type, is_created = SourceType.objects.get_or_create(name='PayPal')
        source = Source(source_type=source_type,
                        currency=txn.currency,
                        amount_allocated=txn.amount,
                        amount_debited=txn.amount)
        self.add_payment_source(source)

    def create_shipping_address(self, basket=None):
        """
        Return a created shipping address instance, created using
        the data returned by PayPal.
        """
        # Determine names - PayPal uses a single field
        ship_to_name = self.txn.value('PAYMENTREQUEST_0_SHIPTONAME')
        if not ship_to_name:
            return

        first_name = last_name = None
        parts = ship_to_name.split()
        if len(parts) == 1:
            last_name = ship_to_name
        elif len(parts) > 1:
            first_name = parts[0]
            last_name = " ".join(parts[1:])

        return ShippingAddress.objects.create(
            first_name=first_name,
            last_name=last_name,
            line1=self.txn.value('PAYMENTREQUEST_0_SHIPTOSTREET'),
            line4=self.txn.value('PAYMENTREQUEST_0_SHIPTOCITY'),
            state=self.txn.value('PAYMENTREQUEST_0_SHIPTOSTATE'),
            postcode=self.txn.value('PAYMENTREQUEST_0_SHIPTOZIP'),
            country=Country.objects.get(iso_3166_1_a2=self.txn.value('PAYMENTREQUEST_0_SHIPTOCOUNTRYCODE'))
        )

    def get_shipping_method(self, basket=None):
        """
        Return the shipping method used
        """
        if self.txn.value('SHIPPINGOPTIONNAME'):
            charge = D(self.txn.value('PAYMENTREQUEST_0_SHIPPINGAMT'))
            method = FixedPrice(charge)
            basket = basket if basket else self.request.basket
            method.set_basket(basket)
            method.name = self.txn.value('SHIPPINGOPTIONNAME')
            return method
        return super(SuccessResponseView, self).get_shipping_method(basket)


class ShippingOptionsView(View):

    def get(self, request, *args, **kwargs):
        """
        We use the shipping address given to use by PayPal to
        determine the available shipping method
        """
        # Basket ID is passed within the URL path.  We need to do this as some
        # shipping options depend on the user and basket contents.  PayPal do
        # pass back details of the basket contents but it would be royal pain to
        # reconstitute the basket based on those - easier to just to piggy-back
        # the basket ID in the callback URL.
        basket = get_object_or_404(Basket, id=kwargs['basket_id'])
        user = basket.owner
        if not user:
            user = AnonymousUser()

        # Create a shipping address instance using the data passed back
        shipping_address = ShippingAddress(
            line1=self.request.GET.get('PAYMENTREQUEST_0_SHIPTOSTREET', None),
            line2=self.request.GET.get('PAYMENTREQUEST_0_SHIPTOSTREET2', None),
            line4=self.request.GET.get('PAYMENTREQUEST_0_SHIPTOCITY', None),
            state=self.request.GET.get('PAYMENTREQUEST_0_SHIPTOSTATE', None),
            postcode=self.request.GET.get('PAYMENTREQUEST_0_SHIPTOZIP', None),
            country=Country.objects.get(iso_3166_1_a2=self.txn.value('PAYMENTREQUEST_0_SHIPTOCOUNTRY'))
        )
        methods = self.get_shipping_methods(user, basket, shipping_address)
        return self.render_to_response(methods)

    def render_to_response(self, methods):
        pairs = [
            ('METHOD', 'CallbackResponse'),
        ]
        for index, method in enumerate(methods):
            pairs.append(('L_SHIPPINGOPTIONNAME%d' % index, method.name))
            pairs.append(('L_SHIPPINGOPTIONAMOUNT%d' % index,
                          method.basket_charge_incl_tax()))
            # For now, we assume tax and insurance to be zero
            pairs.append(('L_TAXAMT%d' % index, D('0.00')))
            pairs.append(('L_INSURANCEAMT%d' % index, D('0.00')))
            # We assume that the first returned method is the default one
            pairs.append(('L_SHIPPINGOPTIONISDEFAULT%d' % index, 1 if index == 0 else 0))
        else:
            # No shipping methods available - we flag this up to PayPal indicating that we
            # do not ship to the shipping address.
            pairs.append(('NO_SHIPPING_OPTION_DETAILS', 1))
        payload = urllib.urlencode(pairs)
        return HttpResponse(payload)

    def get_shipping_methods(self, user, basket, shipping_address):
        repo = Repository()
        return repo.get_shipping_methods(user, basket,
                                         shipping_addr=shipping_address)
