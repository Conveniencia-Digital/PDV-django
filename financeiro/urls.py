from django.contrib.auth.decorators import login_required
from django.urls import path

from financeiro.views import (
    DetalheFinanceiro,
    DetalheFinanceiroOrcamento,
    DetalheFinanceiroVenda,
    ListaContasAReceber,
    apagarcontas_a_receber,
    cadastrarcontas_a_receber,
    editarcontas_a_receber,
)

urlpatterns = [
    path('financeiro', login_required(ListaContasAReceber.as_view()), name='financeiro'),
    path('cadastrarcontas_a_receber/', login_required(cadastrarcontas_a_receber), name='cadastrar-contas-a-receber'),
    path('editarcontas_a_receber/<int:pk>/', login_required(editarcontas_a_receber), name='editar-contas-a-receber'),
    path('apagarcontas_a_receber/<int:pk>/', login_required(apagarcontas_a_receber), name='apagar-contas-a-receber'),
    path('detalhefinanceiro/<int:pk>/', login_required(DetalheFinanceiro.as_view()), name='detalhe-financeiro'),
    path(
        'detalhefinanceirovenda/<int:pk>/',
        login_required(DetalheFinanceiroVenda.as_view()),
        name='detalhe-financeiro-venda',
    ),
    path(
        'detalhefinanceiroorcamento/<int:pk>/',
        login_required(DetalheFinanceiroOrcamento.as_view()),
        name='detalhe-financeiro-orcamento',
    ),
]
