from hashlib import sha1
from django.conf import settings

def compute_signature_hash(params, certifcate):
    """
    Compute the signature according to the doc
    """
    sign = '+'.join(params) + '+' + getattr(settings, 'SYSTEMPAY_CERTIFICATE', '')
    return sha1(sign).hexdigest()