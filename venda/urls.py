from django.urls import path
from venda.views import vendas, buscarpreco, addform, Sale

urlpatterns = [
    path('sale/', Sale.as_view(), name='sale'),
    path('vendas/', vendas, name='vendas'),
    path('produto/preco/', buscarpreco, name='preco-produto'),
    path('addform/', addform, name='addform'),
]
