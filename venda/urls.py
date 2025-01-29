from django.contrib.auth.decorators import login_required
from django.urls import path

from venda.views import (
    DetalheVendas,
    ListaVendas,
    addform,
    apagaritemvenda,
    buscarpreco,
    cadastrarvendas,
    editarvendas,
    valor_total_vendas,
)

urlpatterns = [
    path('vendas/', login_required(ListaVendas.as_view()), name='vendas'),
    path('cadastrarvendas/', login_required(cadastrarvendas), name='cadastrar-vendas'),
    path('editarvendas/<int:pk>/', login_required(editarvendas), name='editar-vendas'),
    path('produto/preco/', login_required(buscarpreco), name='preco-produto'),
    path('addform/', login_required(addform), name='addform'),
    path('apagaritemvenda/', login_required(apagaritemvenda), name='apagar-item-venda'),
    path('detalhevendas/<int:pk>', login_required(DetalheVendas.as_view()), name='detalhe-vendas'),
    path('totalvendas/', valor_total_vendas, name='total-vendas')
]
