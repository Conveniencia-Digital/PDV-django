from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from usuarios.forms import SignUpForm
from django.http import HttpResponseBadRequest, JsonResponse



class SignUp(CreateView):
    template_name = 'registration/form-cadastro.html'
    form_class = SignUpForm
    success_url = reverse_lazy('login')

    