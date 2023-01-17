from django.urls import path
from fornecedor.views import ListaFornecedor, cadastrarfornecedor, editarfornecedor, apagarfornecedor, total_fornecedor


urlpatterns = [
    path('fornecedor/', ListaFornecedor.as_view(), name='fornecedor'),
    path('cadastrarfornecedor/', cadastrarfornecedor, name='cadastrar-fornecedor'),
    path('editarfornecedor/<int:pk>', editarfornecedor, name='editar-fornecedor'),
    path('apagarfornecedor/<int:pk>/', apagarfornecedor, name='apagar-fornecedor'),
    path('totalfornecedor/', total_fornecedor, name='total-fornecedor')
]
