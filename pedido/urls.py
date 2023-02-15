from django.urls import path
from django.contrib.auth.decorators import login_required
from pedido.views import cadastrarpedido, editarpedido, ListaPedido, apagarpedido


urlpatterns = [
    path('cadastrarpedido', login_required(cadastrarpedido), name='cadastrar-pedido'),
    path('editarpedido/<int:pk>/', login_required(editarpedido), name='editar-pedido'),
    path('apagarpedido/<int:pk>/', login_required(apagarpedido), name='apagar-pedido'),
    path('pedido', login_required(ListaPedido.as_view()), name='pedido'),
]