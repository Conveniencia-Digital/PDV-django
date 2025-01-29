from django.contrib.auth.decorators import login_required
from django.urls import path

from pedido.views import DetalhePedido, ListaPedido, apagarpedido, cadastrarpedido, editarpedido

urlpatterns = [
    path('cadastrarpedido', login_required(cadastrarpedido), name='cadastrar-pedido'),
    path('editarpedido/<int:pk>/', login_required(editarpedido), name='editar-pedido'),
    path('apagarpedido/<int:pk>/', login_required(apagarpedido), name='apagar-pedido'),
    path('pedido', login_required(ListaPedido.as_view()), name='pedido'),
    path('detalhepedido/<int:pk>/', DetalhePedido.as_view(), name='detalhe-pedido')
]
