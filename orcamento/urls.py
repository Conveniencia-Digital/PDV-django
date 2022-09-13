from django.urls import path
from orcamento.views import ListaOrcamento, cadastrarorcamento

urlpatterns = [
    path('orcamento/', ListaOrcamento.as_view(), name='orcamento'),
    path('cadastrarorcamento/', cadastrarorcamento, name='cadastrar-orcamento')
]
