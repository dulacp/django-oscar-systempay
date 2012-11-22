from decimal import Decimal as D
from mock import Mock

from django.conf import settings
from django.test import TestCase
from django.http import QueryDict

from systempay.facade import Facade
from systempay.forms import SystemPaySubmitForm, SystemPayReturnForm


class TestForm(TestCase):

    def setUp(self):
        self.order = self.create_mock_order()
        self.facade = Facade()

    def create_mock_order(self):
        order = Mock()
        order.number = '100313'
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

        # override to have the same hash
        self.facade.gateway._site_id = "12345678"
        self.facade.gateway._certificate = "1122334455667788"

        # we sign AGAIN the form because the data has been changed
        self.facade.gateway.sign(form)
        return form

    def printable_form_errors(self, form):
        return u' / '.join([u"%s: %s" % (f.name, '. '.join(f.errors)) for f in form])


class TestSubmitForm(TestForm):

    def test_is_signature_valid(self):
        form = self.create_submit_form_with_order(self.order)
        self.assertTrue( form.is_valid(), msg=u"Errors: %s" % self.printable_form_errors(form) )
        self.assertEqual( len(form.cleaned_data['signature']), 40 )
        self.assertEqual( form.cleaned_data['signature'], '5e1c92ed97089f3192c8c729236ec87567048590' )


class TestReturnForm(TestForm):

    def setUp(self):
        super(TestReturnForm, self).setUp()
        self.request = self.create_mock_request()

    def create_mock_request(self):
        request = Mock()
        request.POST = QueryDict("vads_validation_mode=0&vads_cust_cell_phone=&vads_threeds_error_code=&\
vads_auth_number=171970&vads_site_id=99878789&vads_cust_id=&vads_ctx_mode=TEST&vads_language=fr&\
vads_payment_config=SINGLE&vads_ship_to_name=&vads_threeds_cavv=Q2F2dkNhdnZDYXZ2Q2F2dkNhdnY%3D&vads_extra_result=&\
vads_version=V2&vads_cust_country=&vads_cust_city=&vads_auth_mode=FULL&vads_trans_id=550758&vads_contrib=&\
vads_threeds_xid=dkNBQURpbHluUHMzbHdqSnRsSnc%3D&vads_card_country=FR&vads_cust_phone=&vads_order_info=&\
vads_cust_address=&vads_ship_to_phone_num=&vads_currency=978&vads_page_action=PAYMENT&vads_cust_name=&\
vads_sequence_number=1&vads_order_info2=&vads_order_info3=&\
vads_payment_certificate=f59522596f05f1b18e878f586ea31b4809832969&vads_threeds_enrolled=Y&\
vads_trans_date=20121122151746&vads_url_check_src=PAY&vads_warranty_result=YES&vads_auth_result=00&\
vads_payment_src=EC&vads_threeds_exit_status=10&vads_cust_zip=&vads_card_brand=CB&vads_pays_ip=FR&\
vads_capture_delay=0&vads_ship_to_street=&vads_ship_to_state=&vads_cust_email=&vads_contract_used=5830136&\
vads_action_mode=INTERACTIVE&vads_ship_to_street2=&vads_user_info=&vads_threeds_status=Y&vads_amount=1904&\
vads_order_id=100368&vads_ship_to_zip=&vads_ship_to_country=&vads_threeds_eci=05&vads_cust_state=&\
vads_threeds_sign_valid=1&vads_expiry_year=2013&vads_effective_amount=1904&vads_expiry_month=6&\
vads_threeds_cavvAlgorithm=2&vads_result=00&vads_operation_type=DEBIT&vads_cust_title=&\
signature=33f7eb8ca557cf862c72261da4e602f9c903afc2&vads_trans_status=AUTHORISED&\
vads_theme_config=&vads_ship_to_city=&vads_hash=rcI8uquHGoTJ69krXVkmBDSydSIoFJs2ZE8S26Xt4DQ-&\
vads_card_number=497010XXXXXX0000")  
        return request

    def test_is_signature_valid(self):
        form = self.facade.get_return_form_populated_with_request(self.request)
        # form.is_valid()
        # print form.compute_signature()$
        self.assertTrue( form.is_valid(), msg=u"Errors: %s" % self.printable_form_errors(form) )
        self.assertEqual( len(form.cleaned_data['signature']), 40 )
        self.assertTrue( self.facade.gateway.is_signature_valid(form), msg=u"data: %s, excepted: %s" % (
            form.cleaned_data['signature'], self.facade.gateway.compute_signature(form)) )

