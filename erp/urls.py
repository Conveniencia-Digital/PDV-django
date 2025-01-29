from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('produto.urls')),
    path('', include('dashboard.urls')),
    path('', include('venda.urls')),
    path('', include('peca.urls')),
    path('', include('cliente.urls')),
    path('', include('colaborador.urls')),
    path('', include('despesa.urls')),
    path('', include('financeiro.urls')),
    path('', include('relatorio.urls')),
    path('', include('configuracao.urls')),
    path('', include('orcamento.urls')),
    path('', include('usuarios.urls')),
    path('', include('fornecedor.urls')),
    path('', include('comunidade.urls')),
    path('', include('suporte.urls')),
    path('', include('pedido.urls')),
    path('', include('lanhouse.urls')),

]
