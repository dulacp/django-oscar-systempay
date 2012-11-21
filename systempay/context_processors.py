from systempay.gateway import Gateway

def gateway(request):
  return {
    'SYSTEMPAY_GATEWAY_URL': Gateway.URL
  }