from django.urls import path
from peca.views import Peca, cadastrarpeca, apagarpeca, editarpeca, relatoriopeca
from django.contrib.auth.decorators import login_required

urlpatterns = [
    path('pecas/', login_required(Peca.as_view()), name='pecas'),
    path('cadastrarpeca/', login_required(cadastrarpeca), name='cadastrar-peca'),
    path('editarpeca/<int:pk>/', login_required(editarpeca), name='editar-peca'),
    path('apagarpeca/<int:pk>/', login_required(apagarpeca), name='apagar-peca'),
    path('informacao-peca/', login_required(relatoriopeca), name='relatorio-peca'),
   

]

