from django.urls import path, include
from usuarios.views import SignUp


urlpatterns = [
    path('accounts/', include('django.contrib.auth.urls')),
    path('cadastrar/', SignUp.as_view(), name='cadastrar')
    
]
