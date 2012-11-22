from django import forms


class ResponseForm(forms.Form):

    #################
    # Required params
    #

    ACTION_MODE_INTERACTIVE, ACTION_MODE_SILENT = ('INTERACTIVE', 'SILENT')
    ACTION_MODE_CHOICES = (
            (ACTION_MODE_INTERACTIVE, 'INTERACTIVE'),
            (ACTION_MODE_SILENT, 'SILENT'),
        )
    vads_action_mode = forms.ChoiceField(choices=ACTION_MODE_CHOICES)
    vads_amount = forms.CharField(max_length=12) # NB: expressed in cents for euros (unity undivisible)
    vads_currency = forms.CharField(max_length=3) # 978 stands for EURO (ISO 639-1)

    CONTEXT_TEST, CONTEXT_PRODUCTION = ('TEST', 'PRODUCTION')
    CONTEXT_CHOICES = (
            (CONTEXT_TEST, u"TEST"),
            (CONTEXT_PRODUCTION, u"PRODUCTION")
        )
    vads_ctx_mode = forms.ChoiceField(choices=CONTEXT_CHOICES)

    # needs to be formated as SINGLE or MULTI:first=val1;count=val2;period=val3
    # example: MULTI:first=5000;count=3;period=30 
    #          would represent a payment segmented with a first account of 50,00
    #          then the rest of the amount would be divided in (count-1) other payments
    #          with a timelapse of 30 days between them
    #
    # NB: if the validity date of the credit card can't handle the last payment (in case of multi)
    #     the whole transaction will be rejected
    vads_payment_config = forms.CharField(max_length=127)

    vads_site_id = forms.CharField(min_length=8, max_length=8)

    # Need to respect the format ``YYYYMMDDHHMMSS`` in UTC timezone
    vads_trans_date = forms.CharField(min_length=14, max_length=14)

    # Unique identifier in the range 000000 to 899999. Integer between 900000 and 999999 are reserved
    # NB: it should only be unique over the current day
    vads_trans_id = forms.CharField(min_length=6, max_length=6)
    vads_version = forms.CharField(max_length=8)
    signature = forms.CharField(min_length=40, max_length=40)

    #################
    # Optional params
    #

    vads_capture_delay = forms.CharField(max_length=3, required=False)

    vads_cust_address = forms.CharField(max_length=255, required=False)
    vads_cust_country = forms.CharField(max_length=2, required=False)
    vads_cust_email = forms.CharField(max_length=127, required=False)
    vads_cust_id = forms.CharField(max_length=63, required=False)
    vads_cust_name = forms.CharField(max_length=127, required=False)
    vads_cust_cell_phone = forms.CharField(max_length=32, required=False)
    vads_cust_phone  = forms.CharField(max_length=32, required=False)
    vads_cust_title  = forms.CharField(max_length=63, required=False)
    vads_cust_city = forms.CharField(max_length=63, required=False)
    vads_cust_status = forms.CharField(max_length=63, required=False)
    vads_cust_state = forms.CharField(max_length=63, required=False)
    vads_cust_zip = forms.CharField(max_length=63, required=False)
    vads_language = forms.CharField(max_length=2, required=False)

    vads_order_id = forms.CharField(max_length=32, required=False)
    vads_order_info = forms.CharField(max_length=255, required=False)
    vads_order_info2 = forms.CharField(max_length=255, required=False)
    vads_order_info3 = forms.CharField(max_length=255, required=False)

    vads_validation_mode = forms.CharField(max_length=1, required=False)

    def signature_params(self, data):
        raise NotImplementedError

    def sorted_signature_params(self, data):
        return sorted(p for p in self.signature_params(data) if p.startswith('vads_'))

    def values_for_signature(self, data):
        return tuple( map( str, (data.get(param, '') for param in self.sorted_signature_params(data)) ) )


class SystemPaySubmitForm(ResponseForm):

    vads_page_action = forms.CharField(max_length=8)
    vads_contrib = forms.CharField(max_length=255, required=False)
    vads_payment_cards = forms.CharField(max_length=127, required=False)

    RETURN_MODE_NONE, RETURN_MODE_GET, RETURN_MODE_POST = ('NONE', 'GET', 'POST')
    RETURN_MODE_CHOICES = (
            (RETURN_MODE_NONE, 'NONE'),
            (RETURN_MODE_GET, 'GET'),
            (RETURN_MODE_POST, 'POST'),
        )
    vads_return_mode = forms.ChoiceField(choices=RETURN_MODE_CHOICES, required=False)

    vads_theme_config = forms.CharField(max_length=255, required=False) # Can be used to customize the aspect of the transaction page

    vads_url_success = forms.CharField(max_length=127, required=False)
    vads_url_referral = forms.CharField(max_length=127, required=False)
    vads_url_refused = forms.CharField(max_length=127, required=False)
    vads_url_cancel = forms.CharField(max_length=127, required=False)
    vads_url_error = forms.CharField(max_length=127, required=False)
    vads_url_return = forms.CharField(max_length=127, required=False)

    vads_user_info = forms.CharField(max_length=255, required=False)
    vads_contracts = forms.CharField(max_length=255, required=False)

    redirect_success_timeout = forms.CharField(max_length=3, required=False)
    redirect_success_message = forms.CharField(max_length=255, required=False)
    redirect_error_timeout = forms.CharField(max_length=3, required=False)
    redirect_error_message = forms.CharField(max_length=255, required=False)

    vads_ship_to_city = forms.CharField(max_length=63, required=False)
    vads_ship_to_country = forms.CharField(max_length=2, required=False)
    vads_ship_to_name = forms.CharField(max_length=127, required=False)
    vads_ship_to_phone_num = forms.CharField(max_length=32, required=False)
    vads_ship_to_state = forms.CharField(max_length=255, required=False)
    vads_ship_to_street = forms.CharField(max_length=255, required=False)
    vads_ship_to_street2 = forms.CharField(max_length=255, required=False)
    vads_ship_to_zip = forms.CharField(max_length=63, required=False)

    def signature_params(self, data):
        return self.fields.keys()


class SystemPayReturnForm(ResponseForm):

    vads_effective_amount = forms.CharField(max_length=14, required=False)
    vads_auth_result = forms.CharField(min_length=2, max_length=2, required=False)

    AUTH_MODE_MARK, AUTH_MODE_FULL = ('MARK', 'FULL')
    AUTH_MODE_CHOICES = (
            (AUTH_MODE_MARK, u"MARK"),
            (AUTH_MODE_FULL, u"FULL")
        )
    vads_auth_mode = forms.ChoiceField(choices=AUTH_MODE_CHOICES)
    vads_auth_number = forms.CharField(min_length=6, max_length=6, required=False)

    vads_card_brand = forms.CharField(max_length=127, required=False)
    vads_card_number = forms.CharField(max_length=19, required=False)

    vads_extra_result = forms.CharField(min_length=2, max_length=2, required=False)

    OPERATION_TYPE_EMPTY, OPERATION_TYPE_DEBIT, OPERATION_TYPE_CREDIT = ('', 'DEBIT', 'CREDIT')
    OPERATION_TYPE_CHOICES = (
            (OPERATION_TYPE_EMPTY, ''),
            (OPERATION_TYPE_DEBIT, 'DEBIT'),
            (OPERATION_TYPE_CREDIT, 'CREDIT'),
        )
    vads_operation_type = forms.CharField(max_length=8, required=False)

    vads_sequence_number = forms.CharField(max_length=3, required=False)

    TRANS_STATUS_ABANDONED = 'ABANDONED'
    TRANS_STATUS_AUTHORISED = 'AUTHORISED'
    TRANS_STATUS_REFUSED = 'REFUSED'
    TRANS_STATUS_AUTHORISED_TO_VALIDATE = 'AUTHORISED_TO_VALIDATE'
    TRANS_STATUS_WAITING_AUTHORISATION = 'WAITING_AUTHORISATION'
    TRANS_STATUS_EXPIRED = 'EXPIRED'
    TRANS_STATUS_CANCELLED = 'CANCELLED'
    TRANS_STATUS_WAITING_AUTHORISATION_TO_VALIDATE = 'WAITING_AUTHORISATION_TO_VALIDATE'
    TRANS_STATUS_CAPTURED = 'CAPTURED'
    TRANS_STATUS_CHOICES = (
            (TRANS_STATUS_ABANDONED, 'ABANDONED'),
            (TRANS_STATUS_AUTHORISED, 'AUTHORISED'),
            (TRANS_STATUS_REFUSED, 'REFUSED'),
            (TRANS_STATUS_AUTHORISED_TO_VALIDATE, 'AUTHORISED_TO_VALIDATE'),
            (TRANS_STATUS_WAITING_AUTHORISATION, 'WAITING_AUTHORISATION'),
            (TRANS_STATUS_EXPIRED, 'EXPIRED'),
            (TRANS_STATUS_CANCELLED, 'CANCELLED'),
            (TRANS_STATUS_WAITING_AUTHORISATION_TO_VALIDATE, 'WAITING_AUTHORISATION_TO_VALIDATE'),
            (TRANS_STATUS_CAPTURED, 'CAPTURED'),
        )
    vads_trans_status = forms.ChoiceField(choices=TRANS_STATUS_CHOICES, required=False)

    WARRANTY_RESULT_EMPTY, WARRANTY_RESULT_YES, WARRANTY_RESULT_NO, WARRANTY_RESULT_UNKNOWN = (
            '', 'YES', 'NO', 'UNKNOWN'
        )
    WARRANTY_RESULT_CHOICES = (
            (WARRANTY_RESULT_EMPTY, u""),
            (WARRANTY_RESULT_YES, u"YES"),
            (WARRANTY_RESULT_NO, u"NO"),
            (WARRANTY_RESULT_UNKNOWN, u"UNKNOWN"),
        )
    vads_warranty_result = forms.ChoiceField(choices=WARRANTY_RESULT_CHOICES, required=False)
    vads_payment_certificate = forms.CharField(max_length=40, required=False)
    vads_result = forms.CharField(min_length=2, max_length=2, required=False)
    
    # Used only for pear to pear communication (like the payment notification communicate from server to server)
    vads_hash = forms.CharField(max_length=255, required=False)

    vads_contract_used = forms.CharField(max_length=250, required=False)
    vads_expiry_month = forms.CharField(max_length=2, required=False)
    vads_expiry_year = forms.CharField(max_length=4, required=False)
    vads_threeds_enrolled = forms.CharField(max_length=1, required=False)
    vads_threeds_cavv = forms.CharField(max_length=28, required=False)
    vads_threeds_eci = forms.CharField(max_length=2,  required=False)
    vads_threeds_xid = forms.CharField(max_length=28, required=False)
    vads_threeds_cavvAlgorithm = forms.CharField(max_length=1, required=False)
    vads_threeds_status = forms.CharField(max_length=1, required=False)
    vads_threeds_sign_valid = forms.CharField(max_length=1, required=False)
    vads_threeds_error_code = forms.CharField(max_length=127, required=False)
    vads_threeds_exit_status = forms.CharField(max_length=127, required=False)

    def signature_params(self, data):
        return data.keys()


class SystemPayIPNForm(SystemPayReturnForm):
    #SIGNATURE_PARAMS = SystemPayReturnForm.SIGNATURE_PARAMS + ('hash',)
    pass
