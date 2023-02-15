from django.urls import path
from despesa.views import ListaDespesa, cadastrardespesa, editardespesa, apagardespesa, cadastrarcategoriadespesa, ListaCategoriaDespesa, apagarcategoriadespesa, editarcatergoriadespesa
from django.contrib.auth.decorators import login_required


urlpatterns = [
    path('despesa/', login_required(ListaDespesa.as_view()), name='despesa'),
    path('categoriadespesa/', login_required(cadastrarcategoriadespesa), name='categoria-despesa'),
    path('cadastrardespesa/', login_required(cadastrardespesa), name='cadastrar-despesa'),
    path('editardespesa/<int:pk>/', login_required(editardespesa), name='editar-despesa'),
    path('apagardespesa/<int:pk>/', login_required(apagardespesa), name='apagar-despesa'),
    path('listacategoriadespesa/', login_required(ListaCategoriaDespesa.as_view()), name='lista-categoria-despesa'),
    path('apagarcategoriadespesa/<int:pk>/', login_required(apagarcategoriadespesa), name='apagar-categoria-despesa'),
    path('editarcategoriadespesa/<int:pk>/', login_required(editarcatergoriadespesa), name= 'editar-categoria-despesa')
   
]
