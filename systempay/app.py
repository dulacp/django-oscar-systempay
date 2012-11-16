from django.conf.urls import patterns, url
from oscar.core.application import Application

from systempay import views


class SystemPayApplication(Application):
    name = 'systempay' 

    secure_redirect_view = views.SecureRedirectView
    preview_view = views.PreviewView
    cancel_response_view = views.CancelResponseView
    success_response_view = views.SuccessResponseView

    def __init__(self, *args, **kwargs):
        super(SystemPayApplication, self).__init__(*args, **kwargs)

    def get_urls(self):
        urlpatterns = super(SystemPayApplication, self).get_urls()
        urlpatterns += patterns('',
            url(r'^secure-redirect/', self.secure_redirect_view.as_view(), name='systempay-redirect'),
            url(r'^preview/', self.preview_view.as_view(preview=True),
                name='systempay-success-response'),
            url(r'^cancel/', self.cancel_response_view.as_view(),
                name='systempay-cancel-response'),
            url(r'^place-order/', self.success_response_view.as_view(),
                name='systempay-place-order'),
            # View for using PayPal as a payment method
            # url(r'^handle-ipn/', self.redirect_view.as_view(as_payment_method=True),
            #     name='systempay-direct-payment'),
        )
        return self.post_process_urls(urlpatterns)


application = SystemPayApplication()
