from django.urls import path

from configuracao.views import Configuracao

urlpatterns = [path('configuracao', Configuracao.as_view(), name='configuracao')]
