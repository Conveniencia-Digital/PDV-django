from django.urls import path
from django.contrib.auth.decorators import login_required
from configuracao.views import Configuracao, cadastrar_taxas

urlpatterns = [
    path('configuracao', Configuracao.as_view(), name='configuracao'),
    # urls.py
    path("taxas/", login_required(cadastrar_taxas), name="cadastrar_taxas"),

]
