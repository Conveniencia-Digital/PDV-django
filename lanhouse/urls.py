from django.contrib.auth.decorators import login_required
from django.urls import path

from lanhouse.views import (
    ListaLanhouse,
    ListaServicoLanhouse,
    additemlanhouse,
    apagarservicolanhouse,
    cadastrarlanhouse,
    cadastrarservicolanhouse,
    editarservicolanhouse,
    precoservicolanhouse,
    relatorio_lanhouse,
)

urlpatterns = [
    path('lanhouse/', login_required(ListaLanhouse.as_view()), name='lanhouse'),
    path('cadastrarlanhouse/', login_required(cadastrarlanhouse), name='cadastrar-lanhouse'),
    path('cadastrarservicolanhouse/', login_required(cadastrarservicolanhouse), name='cadastrar-servico-lanhouse'),
    path('additemlanhouse/', login_required(additemlanhouse), name='add-item-lanhouse'),
    path('listaservicolanhouse/', login_required(ListaServicoLanhouse.as_view()), name='lista-servico-lanhouse'),
    path('apagarservicolanhouse/<int:pk>/', login_required(apagarservicolanhouse), name='apagar-servico-lanhouse'),
    path('editarservicolanhouse/<int:pk>/', login_required(editarservicolanhouse), name='editar-servico-lanhouse'),
    path('servico/lanhouse/preco/', login_required(precoservicolanhouse), name='preco-produto'),
    path('relatoriolanhouse/', relatorio_lanhouse, name='relatorio-lanhouse'),
]
