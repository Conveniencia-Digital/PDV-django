from django.urls import path
from relatorio.views import Relatorios

urlpatterns = [
    path('relatorio', Relatorios.as_view(), name='relatorio')
]
