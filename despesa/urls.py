from django.contrib.auth.decorators import login_required
from django.urls import path

from despesa.views import (
    DetalheDespesa,
    DetalheDespesaPeca,
    DetalheDespesaProduto,
    ListaCategoriaDespesa,
    ListaDespesa,
    apagarcategoriadespesa,
    apagardespesa,
    cadastrarcategoriadespesa,
    cadastrardespesa,
    editarcatergoriadespesa,
    editardespesa,
)

urlpatterns = [
    path('despesa/', login_required(ListaDespesa.as_view()), name='despesa'),
    path('categoriadespesa/', login_required(cadastrarcategoriadespesa), name='categoria-despesa'),
    path('cadastrardespesa/', login_required(cadastrardespesa), name='cadastrar-despesa'),
    path('editardespesa/<int:pk>/', login_required(editardespesa), name='editar-despesa'),
    path('apagardespesa/<int:pk>/', login_required(apagardespesa), name='apagar-despesa'),
    path('listacategoriadespesa/', login_required(ListaCategoriaDespesa.as_view()), name='lista-categoria-despesa'),
    path('apagarcategoriadespesa/<int:pk>/', login_required(apagarcategoriadespesa), name='apagar-categoria-despesa'),
    path('editarcategoriadespesa/<int:pk>/', login_required(editarcatergoriadespesa), name='editar-categoria-despesa'),
    path(
        'detalhedespesaproduto/<int:pk>/',
        login_required(DetalheDespesaProduto.as_view()),
        name='detalhe-despesa-produto',
    ),
    path('detalhedespesapeca/<int:pk>/', login_required(DetalheDespesaPeca.as_view()), name='detalhe-despesa-peca'),
    path('detalhedespesa/<int:pk>/', login_required(DetalheDespesa.as_view()), name='detalhe-despesa'),
]
