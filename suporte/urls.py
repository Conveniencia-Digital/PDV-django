from django.urls import path
from suporte.views import SuporteView, enviarsuporte



urlpatterns = [
    path('suporte/', SuporteView.as_view(), name='suporte'),
    path('enviarsuporte/', enviarsuporte, name='enviar-suporte')
]