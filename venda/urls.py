from django.urls import path
from venda.views import cadastrarvendas, buscarpreco, addform, ListaVendas, apagaritemvenda, DetalheVendas

urlpatterns = [
    path('vendas/', ListaVendas.as_view(), name='vendas'),
    path('cadastrarvendas/', cadastrarvendas, name='cadastrar-vendas'),
    path('produto/preco/', buscarpreco, name='preco-produto'),
    path('addform/', addform, name='addform'),
    path('apagaritemvenda/', apagaritemvenda, name='apagar-item-venda'),
    path('detalhevendas/<int:pk>', DetalheVendas.as_view(), name='detalhe-vendas')
]
