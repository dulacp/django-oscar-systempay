from django.conf.urls.defaults import *

from oscar.app import shop

urlpatterns = patterns('',
    (r'^checkout/systempay/', include('systempay.urls')),
    (r'', include(shop.urls)),
)