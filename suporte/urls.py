from django.urls import path
from suporte.views import Suporte, enviarsuporte



urlpatterns = [
    path('suporte/', Suporte.as_view(), name='suporte'),
    path('enviarsuporte/', enviarsuporte, name='enviar-suporte')
]