from django.conf.urls import patterns, url
from oscar.core.application import Application

from systempay.views import *


class SystemPayApplication(Application):
    name = 'systempay' 

    redirect_view = None
    preview_view = None
    cancel_response_view = None
    success_response_view = None

    def __init__(self, *args, **kwargs):
        super(SystemPayApplication, self).__init__(*args, **kwargs)

    def get_urls(self):
        urlpatterns = super(SystemPayApplication, self).get_urls()
        urlpatterns += patterns('',
            url(r'^redirect/', self.redirect_view.as_view(), name='systempay-redirect'),
            url(r'^preview/', self.success_response_view.as_view(preview=True),
                name='systempay-success-response'),
            url(r'^cancel/', self.cancel_response_view.as_view(),
                name='systempay-cancel-response'),
            url(r'^place-order/', self.success_response_view.as_view(),
                name='systempay-place-order'),
            # View for using PayPal as a payment method
            url(r'^payment/', self.redirect_view.as_view(as_payment_method=True),
                name='systempay-direct-payment'),
        )
        return self.post_process_urls(urlpatterns)


application = SystemPayApplication()
