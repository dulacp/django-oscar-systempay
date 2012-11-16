from django import forms

from systempay.utils import compute_signature_hash


class ResponseForm(forms.Form):

    # Needs to be override by subclasses of ResponseForm
    SIGNATURE_PARAMS = tuple()


    # Transaction details used by both SystemPay SEND and RETURN request
    amount = forms.CharField(max_length=12, required=False) # NB: expressed in cents for euros (unity undivisible)
    capture_delay = forms.CharField(max_length=3, required=False)
    currency = forms.CharField(max_length=3) # ISO 421, required=False7

    CONTEXT_TEST, CONTEXT_PRODUCTION = ('TEST', 'PRODUCTION')
    CONTEXT_CHOICES = (
            (CONTEXT_TEST, u"TEST"),
            (CONTEXT_PRODUCTION, u"PRODUCTION")
        )
    ctx_mode = forms.ChoiceField(choices=CONTEXT_CHOICES)

    # needs to be formated as SINGLE or MULTI:first=val1;count=val2;period=val3
    # example: MULTI:first=5000;count=3;period=30 
    #          would represent a payment segmented with a first account of 50,00
    #          then the rest of the amount would be divided in (count-1) other payments
    #          with a timelapse of 30 days between them
    #
    # NB: if the validity date of the credit card can't handle the last payment (in case of multi)
    #     the whole transaction will be rejected
    payment_config = forms.CharField(max_length=127, required=False)

    PAYMENT_SOURCE_EMPTY, PAYMENT_SOURCE_BO, PAYMENT_SOURCE_MOTO, PAYMENT_SOURCE_CC, PAYMENT_SOURCE_OTHER = (
        '', 'BO', 'MOTO', 'CC', 'OTHER')
    PAYMENT_SOURCE_CHOICES = (
            (PAYMENT_SOURCE_EMPTY, u""),
            (PAYMENT_SOURCE_BO, u"BO"),
            (PAYMENT_SOURCE_MOTO, u"MOTO"),
            (PAYMENT_SOURCE_CC, u"CC"),
            (PAYMENT_SOURCE_OTHER, u"OTHER"),
        )
    payment_src = forms.ChoiceField(choices=PAYMENT_SOURCE_CHOICES, required=False)

    signature = forms.CharField(max_length=40, required=False)
    site_id = forms.CharField(min_length=8, max_length=8, required=False)

    # Need to respect the format ``YYYYMMDDHHMMSS`` in UTC timezone
    trans_date = forms.CharField(max_length=14, required=False)

    # Unique identifier in the range 000000 to 899999. Integer between 900000 and 999999 are reserved
    # NB: it should only be unique over the current day
    trans_id = forms.CharField(max_length=6, required=False)
    validation_mode = forms.CharField(max_length=1, required=False)
    version = forms.CharField(max_length=10, required=False)

    order_id = forms.CharField(max_length=32, required=False)
    order_info = forms.CharField(max_length=255, required=False)
    order_info2 = forms.CharField(max_length=255, required=False)
    order_info3 = forms.CharField(max_length=255, required=False)

    cust_address = forms.CharField(max_length=255, required=False)
    cust_country = forms.CharField(min_length=2, max_length=2, required=False)
    cust_email = forms.CharField(max_length=127, required=False)
    cust_id = forms.CharField(max_length=63, required=False)
    cust_name = forms.CharField(max_length=127, required=False)
    cust_phone = forms.CharField(max_length=63, required=False)
    cust_title = forms.CharField(max_length=63, required=False)
    cust_city = forms.CharField(max_length=63, required=False)
    cust_zip = forms.CharField(max_length=63, required=False)

    language = forms.CharField(min_length=2, max_length=2, required=False)
    user_info = forms.CharField(max_length=255, required=False)

    # Can be used to customize the aspect of the transaction page
    theme_config = forms.CharField(max_length=255, required=False)

    def values_for_signature(self, data):
        return tuple(data[param] for param in self.SIGNATURE_PARAMS)


class SystemPaySubmitForm(ResponseForm):

    SIGNATURE_PARAMS = (
            'version', 
            'site_id', 
            'ctx_mode', 
            'trans_id', 
            'trans_date', 
            'validation_mode', 
            'capture_delay', 
            'payment_config', 
            'payment_cards', 
            'amount', 
            'currency',
        )


    # Specific value of a SystemPay SUBMIT request
    contrib = forms.CharField(max_length=255, required=False)

    payment_cards = forms.CharField(max_length=127, required=False)

    url_success = forms.CharField(max_length=127, required=False)
    url_referral = forms.CharField(max_length=127, required=False)
    url_refused = forms.CharField(max_length=127, required=False)
    url_cancel = forms.CharField(max_length=127, required=False)
    url_error = forms.CharField(max_length=127, required=False)
    url_return = forms.CharField(max_length=127, required=False)

    contracts = forms.CharField(max_length=255, required=False)


class SystemPayReturnForm(ResponseForm):

    SIGNATURE_PARAMS = (
            'version',
            'site_id',
            'ctx_mode',
            'trans_id',
            'trans_date',
            'validation_mode',
            'capture_delay',
            'payment_config',
            'card_brand',
            'card_number',
            'amount',
            'currency',
            'auth_mode',
            'auth_result',
            'auth_number',
            'warranty_result',
            'payment_certificate',
            'result',
        )


    auth_result = forms.CharField(min_length=2, max_length=2, required=False)

    AUTH_MODE_MARK, AUTH_MODE_FULL = ('MARK', 'FULL')
    AUTH_MODE_CHOICES = (
            (AUTH_MODE_MARK, u"MARK"),
            (AUTH_MODE_FULL, u"FULL")
        )
    auth_mode = forms.ChoiceField(choices=AUTH_MODE_CHOICES)
    auth_number = forms.CharField(min_length=6, max_length=6, required=False)

    card_brand = forms.CharField(max_length=127, required=False)
    card_number = forms.CharField(max_length=19, required=False)

    extra_result = forms.CharField(min_length=2, max_length=2, required=False)

    WARRANTY_RESULT_EMPTY, WARRANTY_RESULT_YES, WARRANTY_RESULT_NO, WARRANTY_RESULT_UNKNOWN = (
            '', 'YES', 'NO', 'UNKNOWN'
        )
    WARRANTY_RESULT_CHOICES = (
            (WARRANTY_RESULT_EMPTY, u""),
            (WARRANTY_RESULT_YES, u"YES"),
            (WARRANTY_RESULT_NO, u"NO"),
            (WARRANTY_RESULT_UNKNOWN, u"UNKNOWN"),
        )
    warranty_result = forms.ChoiceField(choices=WARRANTY_RESULT_CHOICES, required=False)
    payment_certificate = forms.CharField(max_length=40, required=False)
    result = forms.CharField(min_length=2, max_length=2, required=False)


class SystemPayIPNForm(SystemPayReturnForm):
    SIGNATURE_PARAMS = SystemPayReturnForm.SIGNATURE_PARAMS + ('hash',)
