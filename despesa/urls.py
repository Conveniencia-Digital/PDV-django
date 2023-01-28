from django.urls import path
from despesa.views import ListaDespesa, cadastrardespesa, editardespesa, apagardespesa, CategoriaDespesa
from django.contrib.auth.decorators import login_required


urlpatterns = [
    path('despesa/', login_required(ListaDespesa.as_view()), name='despesa'),
    path('categoriadespesa/', login_required(CategoriaDespesa.as_view()), name='categoria-despesa'),
    path('cadastrardespesa/', login_required(cadastrardespesa), name='cadastrar-despesa'),
    path('editardespesa/<int:pk>/', login_required(editardespesa), name='editar-despesa'),
    path('apagardespesa/<int:pk>/', login_required(apagardespesa), name='apagar-despesa'),
   
]
