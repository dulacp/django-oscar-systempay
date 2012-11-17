class SystemPayFormNotValid(Exception):
    pass

class SystemPayGatewayParamError(Exception):

    ASSOCS = {
        '47': 'vads_action_mode',
        '09': 'vads_amount',
        '10': 'vads_currency',
        '11': 'vads_ctx_mode',
        '46': 'vads_page_action',
        '07': 'vads_payment_config',
        '02': 'vads_site_id',
        '04': 'vads_trans_date',
        '03': 'vads_trans_id',
        '01': 'vads_version',
        '00': 'signature',

        '06': 'vads_capture_delay',
        '31': 'vads_contrib',

        '19': 'vads_cust_address',
        '22': 'vads_cust_country',
        '15': 'vads_cust_email',
        '16': 'vads_cust_id',
        '18': 'vads_cust_name',
        '77': 'vads_cust_cell_phone',
        '23': 'vads_cust_phone ',
        '17': 'vads_cust_title ',
        '21': 'vads_cust_city',
        '92': 'vads_cust_status',
        '88': 'vads_cust_state',
        '20': 'vads_cust_zip',

        '12': 'vads_language',

        '13': 'vads_order_id',
        '14': 'vads_order_info',
        '14': 'vads_order_info2',
        '14': 'vads_order_info3',

        '08': 'vads_payment_cards',
        '48': 'vads_return_mode',
        '32': 'vads_theme_config',
        '05': 'vads_validation_mode',

        '24': 'vads_url_success',
        '26': 'vads_url_referral',
        '25': 'vads_url_refused',
        '27': 'vads_url_cancel',
        '29': 'vads_url_error',
        '28': 'vads_url_return',

        '61': 'vads_user_info',
        '62': 'vads_contracts',

        '34': 'redirect_success_timeout',
        '35': 'redirect_success_message',
        '36': 'redirect_error_timeout',
        '37': 'redirect_error_message',

        '48': 'return_mode',

        '83': 'vads_ship_to_city',
        '86': 'vads_ship_to_country',
        '80': 'vads_ship_to_name',
        '87': 'vads_ship_to_phone_num',
        '84': 'vads_ship_to_state',
        '81': 'vads_ship_to_street',
        '82': 'vads_ship_to_street2',
        '85': 'vads_ship_to_zip',
    }

    def __init__(self, code):
        super(SystemPayGatewayParamError, self).__init__(self, 
                code=code, 
                message=u"The gateway throw the error code '%s' associated to the param '%s'" % (
                    code, self.ASSOCS.get(code, '<unknown>')
                )
            )
