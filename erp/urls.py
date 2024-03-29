"""erp URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include



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


