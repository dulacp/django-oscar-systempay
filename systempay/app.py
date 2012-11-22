from django.conf.urls import patterns, url
from oscar.core.application import Application

from systempay import views


class SystemPayApplication(Application):
    name = 'systempay' 

    secure_redirect_view = views.SecureRedirectView
    place_order_view = views.PlaceOrderView
    return_response_view = views.ReturnResponseView
    cancel_response_view = views.CancelResponseView
    handle_ipn_view = views.HandleIPN

    def __init__(self, *args, **kwargs):
        super(SystemPayApplication, self).__init__(*args, **kwargs)

    def get_urls(self):
        urlpatterns = super(SystemPayApplication, self).get_urls()
        urlpatterns += patterns('',
            url(r'^secure-redirect/', self.secure_redirect_view.as_view(), name='secure-redirect'),
            url(r'^preview/', self.place_order_view.as_view(preview=True),
                name='preview'),
            url(r'^place-order/', self.place_order_view.as_view(),
                name='place-order'),
            url(r'^return/', self.return_response_view.as_view(),
                name='return-response'),
            url(r'^cancel/', self.cancel_response_view.as_view(),
                name='cancel-response'),
            url(r'^handle-ipn$', self.handle_ipn_view.as_view(),
                name='handle-ipn'),
        )
        return self.post_process_urls(urlpatterns)


application = SystemPayApplication()
