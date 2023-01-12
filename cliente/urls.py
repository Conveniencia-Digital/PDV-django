from django.urls import path
from cliente.views import ListaCliente, cadastrarcliente, editarcliente, apagarcliente, total_clientes


urlpatterns = [
    path('cliente/', ListaCliente.as_view(), name='cliente'),
    path('cadastrarcliente/', cadastrarcliente, name='cadastrar-cliente'),
    path('editarcliente/<int:pk>', editarcliente, name='editar-cliente'),
    path('apagarcliente/<int:pk>/', apagarcliente, name='apagar-cliente'),
    path('totalclientes/', total_clientes, name='total-clientes')
]
