from django.urls import path
from .views import PaginaInicialView

urlpatterns = [
    path('', PaginaInicialView.as_view(), name='inicio')
]