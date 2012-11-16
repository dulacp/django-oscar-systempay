from decimal import Decimal as D
from mock import Mock

from django.conf import settings
from django.test import TestCase

from oscar.apps.basket.models import Basket
from systempay.gateway import Gateway
from systempay.forms import SystemPaySubmitForm, SystemPayReturnForm


class TestForm(TestCase):

    def setUp(self):
        self.basket = self.create_mock_basket()
        self.gateway = Gateway(
            'www.example.com', 
            getattr(settings, 'SYSTEMPAY_CONTEXT_MODE'), 
            getattr(settings, 'SYSTEMPAY_SITE_ID')
        )

    def create_mock_basket(self):
        basket = Mock()
        basket.total_incl_tax = D('15.24')
        basket.lines = Mock()
        basket.lines.all = Mock(return_value=[])
        basket.total_discount = D('0.00')
        basket.get_discounts = Mock(return_value=[])
        return basket

    def create_submit_form_with_basket(self, basket):
        form = self.gateway.get_submit_form_populated_with_basket(self.basket)
        form.data['trans_id'] = '654321'
        form.data['trans_date'] = '20090501193530'
        form.data['validation_mode'] = '1'
        form.data['capture_delay'] = '3'
        form.data['payment_config'] = 'SINGLE'
        form.data['payment_cards'] = 'VISA;MASTERCARD'
        return form


class TestSubmitForm(TestForm):

    def test_basket_can_be_submitted(self):
        for line in self.basket.lines.all():
            self.assertTrue( line.product.is_purchase_permitted(self.request.user, line.quantity) )

    def test_required_params_for_signature(self):
        form = self.gateway.get_submit_form_populated_with_basket(self.basket)
        for param in SystemPaySubmitForm.SIGNATURE_PARAMS:
            self.assertIsNotNone( form.fields[param] )

    def test_is_signature_valid(self):
        form = self.create_submit_form_with_basket(self.basket)
        self.assertTrue( form.is_valid() )
        self.assertTrue( form.sign() )
        self.assertEqual( len(form.cleaned_data['signature']), 40 )
        self.assertEqual( form.cleaned_data['signature'], 'a6203523bc029df78f3654fe8569b1f7e293b411' )


class TestReturnForm(TestForm):

    def setUp(self):
        super(TestReturnForm, self).setUp()
        self.request = self.create_mock_request()

    def create_mock_request(self):
        request = Mock()
        submit_form = self.create_submit_form_with_basket(self.basket)
        submit_form.is_valid()
        request.POST = {
            'amount': submit_form.cleaned_data['amount'],
            'auth_result': '',
            'auth_mode': 'FULL',
            'auth_number': '123456',
            'capture_delay': submit_form.cleaned_data['capture_delay'],
            'card_brand': '0123456789',
            'card_number': '987654321',
            'ctx_mode': submit_form.cleaned_data['ctx_mode'],
            'currency': submit_form.cleaned_data['currency'],
            'extra_result': '',
            'payment_config': submit_form.cleaned_data['payment_config'],

            'signature': '485a22902ccb0b92ae1cd38122f70ff81b3c2a5c',

            'site_id': submit_form.cleaned_data['site_id'],
            'trans_id': submit_form.cleaned_data['trans_id'],
            'trans_date': submit_form.cleaned_data['trans_date'],
            'validation_mode': submit_form.cleaned_data['validation_mode'],
            'warranty_result': '',
            'payment_certificate': "0123456789101112131415161718192021222324",
            'result': "02",

            'version': submit_form.cleaned_data['version'],
            'order_id': submit_form.cleaned_data['order_id'],
            'order_info': submit_form.cleaned_data['order_info'],
            'order_info2': submit_form.cleaned_data['order_info2'],
            'order_info3': submit_form.cleaned_data['order_info3'],

            'cust_address': submit_form.cleaned_data['cust_address'],
            'cust_country': submit_form.cleaned_data['cust_country'],
            'cust_email': submit_form.cleaned_data['cust_email'],
            'cust_id': submit_form.cleaned_data['cust_id'],
            'cust_name': submit_form.cleaned_data['cust_name'],
            'cust_phone': submit_form.cleaned_data['cust_phone'],
            'cust_title': submit_form.cleaned_data['cust_title'],
            'cust_city': submit_form.cleaned_data['cust_city'],
            'cust_zip': submit_form.cleaned_data['cust_zip'],

            'language': submit_form.cleaned_data['language'],
            'payment_src': submit_form.cleaned_data['payment_src'],
            'user_info': submit_form.cleaned_data['user_info'],
            'theme_config': submit_form.cleaned_data['theme_config'],

            'contract_used': "CONTRAT" #TODO
        }
        return request

    def test_required_params_for_signature(self):
        form = self.gateway.get_return_form_populated_with_request(self.request)
        for param in SystemPayReturnForm.SIGNATURE_PARAMS:
            self.assertIsNotNone( form.fields[param] )

    def test_is_signature_valid(self):
        form = self.gateway.get_return_form_populated_with_request(self.request)
        # form.is_valid()
        # print form.compute_signature()
        self.assertTrue( form.is_valid(), msg=u"Errors: %s" % form.errors )
        self.assertEqual( len(form.cleaned_data['signature']), 40 )
        self.assertTrue( form.is_signature_valid() )

