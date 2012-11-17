from decimal import Decimal as D
from mock import Mock

from django.conf import settings
from django.test import TestCase

from systempay.facade import Facade
from systempay.forms import SystemPaySubmitForm, SystemPayReturnForm


class TestForm(TestCase):

    def setUp(self):
        self.order = self.create_mock_order()
        self.facade = Facade()

    def create_mock_order(self):
        order = Mock()
        order.id = '100313'
        order.total_incl_tax = D('15.24')
        order.lines = Mock()
        order.lines.all = Mock(return_value=[])
        order.total_discount = D('0.00')
        order.get_discounts = Mock(return_value=[])
        return order

    def create_submit_form_with_order(self, order):
        form = self.facade.get_submit_form_populated_with_order(self.order)
        form.data['vads_trans_id'] = '654321'
        form.data['vads_trans_date'] = '20090501193530'
        form.data['vads_payment_config'] = 'SINGLE'
        return form

    def printable_form_errors(self, form):
        return u' / '.join([u"%s: %s" % (f.name, '. '.join(f.errors)) for f in form])


class TestSubmitForm(TestForm):

    def test_required_params_for_signature(self):
        form = self.facade.get_submit_form_populated_with_order(self.order)
        for param in form.signature_params:
            self.assertIsNotNone( form.fields[param] )

    def test_is_signature_valid(self):
        form = self.create_submit_form_with_order(self.order)
        self.facade.gateway.sign(form)
        self.assertTrue( form.is_valid(), msg=u"Errors: %s" % self.printable_form_errors(form) )
        self.assertEqual( len(form.cleaned_data['signature']), 40 )
        self.assertEqual( form.cleaned_data['signature'], '606b369759fac4f0864144c803c73676cbe470ff' )


class TestReturnForm(TestForm):

    def setUp(self):
        super(TestReturnForm, self).setUp()
        self.request = self.create_mock_request()

    def create_mock_request(self):
        request = Mock()
        request.POST = {}
        submit_form = self.create_submit_form_with_order(self.order)
        request.POST.update(submit_form.data)
        request.POST.update({
            'vads_auth_result': '',
            'vads_auth_mode': 'FULL',
            'vads_auth_number': '123456',
            'vads_card_brand': '0123456789',
            'vads_card_number': '987654321',
            'vads_extra_result': '',

            'signature': 'f3b1b367f02b1fefb9255d3bc1cd9010608d3754',

            'warranty_result': '',
            'payment_certificate': "0123456789101112131415161718192021222324",
            'result': "02",

            'contract_used': "CONTRAT" #TODO
        })
        return request

    def test_required_params_for_signature(self):
        form = self.facade.get_return_form_populated_with_request(self.request)
        for param in form.signature_params:
            self.assertIsNotNone( form.fields[param] )

    def test_is_signature_valid(self):
        form = self.facade.get_return_form_populated_with_request(self.request)
        # form.is_valid()
        # print form.compute_signature()
        self.assertTrue( form.is_valid(), msg=u"Errors: %s" % self.printable_form_errors(form) )
        self.assertEqual( len(form.cleaned_data['signature']), 40 )
        self.assertTrue( self.facade.gateway.is_signature_valid(form), msg=u"data: %s, excepted: %s" % (
            form.cleaned_data['signature'], self.facade.gateway.compute_signature(form)) )

