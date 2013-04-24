from django.conf.urls.defaults import *

from oscar.app import shop
from systempay.app import application as app

urlpatterns = patterns('',
    (r'^checkout/systempay/', include(app.urls)),
    (r'', include(shop.urls)),
)