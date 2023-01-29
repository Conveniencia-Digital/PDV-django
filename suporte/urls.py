from django.urls import path
from suporte.views import Suporte



urlpatterns = [
    path('suporte/', Suporte.as_view(), name='suporte')
]