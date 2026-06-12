from django.urls import path
from financeiro.views import ListaContasAReceber, cadastrarcontas_a_receber, editarcontas_a_receber, \
     apagarcontas_a_receber, DetalheFinanceiro, DetalheFinanceiroVenda, DetalheFinanceiroOrcamento, \
     ListaMaquininhaCartao, cadastrarmaquininhacartao, dashboard_financeiro, \
     desativarmaquininhacartao, editarmaquininhacartao, fechamento_caixa

from django.contrib.auth.decorators import login_required


urlpatterns = [
    path('financeiro/dashboard/', login_required(dashboard_financeiro), name='dashboard-financeiro'),
    path('financeiro/fechamento-caixa/', login_required(fechamento_caixa), name='fechamento-caixa'),
    path('financeiro/maquininhas/', login_required(ListaMaquininhaCartao.as_view()), name='maquininhas-cartao'),
    path('financeiro/maquininhas/cadastrar/', login_required(cadastrarmaquininhacartao), name='cadastrar-maquininha-cartao'),
    path('financeiro/maquininhas/<int:pk>/editar/', login_required(editarmaquininhacartao), name='editar-maquininha-cartao'),
    path('financeiro/maquininhas/<int:pk>/status/', login_required(desativarmaquininhacartao), name='status-maquininha-cartao'),
    path('financeiro', login_required(ListaContasAReceber.as_view()), name='financeiro'),
    path('cadastrarcontas_a_receber/', login_required(cadastrarcontas_a_receber), name='cadastrar-contas-a-receber'),
    path('editarcontas_a_receber/<int:pk>/', login_required(editarcontas_a_receber), name='editar-contas-a-receber'),
    path('apagarcontas_a_receber/<int:pk>/', login_required(apagarcontas_a_receber), name='apagar-contas-a-receber'),
    path('detalhefinanceiro/<int:pk>/', login_required(DetalheFinanceiro.as_view()), name='detalhe-financeiro'),
    path('detalhefinanceirovenda/<int:pk>/', login_required(DetalheFinanceiroVenda.as_view()), name='detalhe-financeiro-venda'),
    path('detalhefinanceiroorcamento/<int:pk>/', login_required(DetalheFinanceiroOrcamento.as_view()), name='detalhe-financeiro-orcamento'),
]
