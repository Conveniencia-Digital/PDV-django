from django.contrib.auth import views as auth_views
from django.urls import include, path

urlpatterns = [
    path('accounts/', include('allauth.urls')),
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
]
