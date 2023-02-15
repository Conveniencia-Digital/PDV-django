from django.urls import path
from cliente.views import ListaCliente, cadastrarcliente, editarcliente, apagarcliente, total_clientes, DetalheClienteView
from django.contrib.auth.decorators import login_required


urlpatterns = [
    path('cliente/', login_required(ListaCliente.as_view()), name='cliente'),
    path('cadastrarcliente/', login_required(cadastrarcliente), name='cadastrar-cliente'),
    path('editarcliente/<int:pk>', login_required(editarcliente), name='editar-cliente'),
    path('apagarcliente/<int:pk>/', login_required(apagarcliente), name='apagar-cliente'),
    path('totalclientes/', login_required(total_clientes), name='total-clientes'),
    path('detalhecliente/<int:pk>/', login_required(DetalheClienteView.as_view()), name='detalhe-cliente')
]
