from django.urls import path
from peca.views import Peca, cadastrarpeca, apagarpeca, editarpeca, relatoriopeca

urlpatterns = [
    path('pecas/', Peca.as_view(), name='pecas'),
    path('cadastrarpeca/', cadastrarpeca, name='cadastrar-peca'),
    path('editarpeca/<int:pk>/', editarpeca, name='editar-peca'),
    path('apagarpeca/<int:pk>/', apagarpeca, name='apagar-peca'),
    path('informacao-peca/', relatoriopeca, name='relatorio-peca'),
   

]

