from xml.dom.minidom import Document, parseString
import httplib
import re
import logging

from oscar.apps.payment.exceptions import GatewayError

logger = logging.getLogger('systempay')

# Methods
AUTH = 'auth'
PRE = 'pre'
REFUND = 'refund'
ERP = 'erp'
CANCEL = 'cancel'
FULFILL = 'fulfill'
TXN_REFUND = 'txn_refund'

# Status codes
ACCEPTED, DECLINED, INVALID_CREDENTIALS = '1', '7', '10'


class Gateway(object):

    def __init__(self, host, client, password, cv2avs=False, capturemethod='ecomm'):
        if host.startswith('http'):
            raise RuntimeError("DATACASH_HOST should not include http")
        self._host = host
        self._client = client
        self._password = password
        self._cv2avs = cv2avs
        self._capturemethod = capturemethod
        