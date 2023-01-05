from django.urls import path
from despesa.views import ListaDespesa, cadastrardespesa, editardespesa, apagardespesa, CategoriaDespesa


urlpatterns = [
    path('despesa/', ListaDespesa.as_view(), name='despesa'),
    path('categoriadespesa/', CategoriaDespesa.as_view(), name='categoria-despesa'),
    path('cadastrardespesa/', cadastrardespesa, name='cadastrar-despesa'),
    path('editardespesa/<int:pk>/', editardespesa, name='editar-despesa'),
    path('apagardespesa/<int:pk>/', apagardespesa, name='apagar-despesa'),
]
