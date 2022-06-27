from django.shortcuts import render
from django.views.generic import CreateView, ListView
from produto.forms import ProdutoForms
from produto.models import Produto
from django.urls import reverse_lazy


# Create your views here.

class ListaProduto(ListView):
    model = Produto
    template_name = 'produto/produto.html'


def criarproduto(request):
    template_name = 'produto/modal-produto-fornece-conteudo.html'
    form = ProdutoForms(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            produto = form.save()
            template_name = 'produto/lista-produto.html'
            context = {'object': produto}
            return render(request, template_name, context)

    context = {'form': form}
    return render(request, template_name, context)

