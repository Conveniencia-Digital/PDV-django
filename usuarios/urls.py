from django.urls import path, include
from usuarios.views import SignUp


urlpatterns = [
    path('accounts/', include('django.contrib.auth.urls')),
    path('register/', SignUp.as_view(), name='register')
    
]
