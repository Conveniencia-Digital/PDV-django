from django.urls import reverse_lazy
from django.views.generic import CreateView
from produto.forms import ProdutoForms

# Create your views here.


class CriarProduto(CreateView):
    form_class = ProdutoForms
    template_name = 'produto/teste.html'
    success_url = ''
