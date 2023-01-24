from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from usuarios.forms import SignUpForm

class SignUp(CreateView):
    template_name = 'registration/login.html'
    form_class = SignUpForm
    success_url = reverse_lazy('login')
