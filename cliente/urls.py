from django.urls import path
from cliente.views import ListaCliente, cadastrarcliente, editarcliente, apagarcliente


urlpatterns = [
    path('cliente/', ListaCliente.as_view(), name='cliente'),
    path('cadastrarcliente/', cadastrarcliente, name='cadastrar-cliente'),
    path('editarcliente/<int:pk>', editarcliente, name='editar-cliente'),
    path('apagarcliente/<int:pk>/', apagarcliente, name='apagar-cliente'),
]
