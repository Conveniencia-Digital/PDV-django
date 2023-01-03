from django.urls import path
from .views import PaginaInicialView
from django.contrib.auth.decorators import login_required

urlpatterns = [
    path('', login_required(PaginaInicialView.as_view()), name='inicio')
]