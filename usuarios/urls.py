from django.urls import path, include
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('accounts/', include('allauth.urls')),
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
]