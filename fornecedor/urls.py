from django.urls import path
from django.contrib.auth.decorators import login_required
from fornecedor.views import ListaFornecedor, cadastrarfornecedor, editarfornecedor, apagarfornecedor, total_fornecedor, DetalheFornecedorView


urlpatterns = [
    path('fornecedor/', login_required(ListaFornecedor.as_view()), name='fornecedor'),
    path('cadastrarfornecedor/', login_required(cadastrarfornecedor), name='cadastrar-fornecedor'),
    path('editarfornecedor/<int:pk>', login_required(editarfornecedor), name='editar-fornecedor'),
    path('apagarfornecedor/<int:pk>/', login_required(apagarfornecedor), name='apagar-fornecedor'),
    path('totalfornecedor/', login_required(total_fornecedor), name='total-fornecedor'),
    path('detalhefornecedor/<int:pk>/', login_required(DetalheFornecedorView.as_view()), name='detalhe-fornecedor')
]
