from django.shortcuts import render
from django.views.generic import ListView

from produto.forms import ProdutoForms
from produto.models import Produto
from django.contrib.auth.decorators import login_required

class ListaProduto(ListView):
    model = Produto
    template_name = 'produto/pagina-inicial-produto.html'

    def get_queryset(self):
        return Produto.objects.filter(usuario=self.request.user)


@login_required
def criarprodutos(request):
    template_name = 'produto/formularios/formulario-cadastrar-produto.html'
    form = ProdutoForms(request.POST or None, initial={'usuario': request.user})

    if request.method == 'POST':
        if form.is_valid():
            produto = form.save()
            template_name = 'produto/tabela/linhas-tabela-produto.html'

            context = {'object': produto}
            return render(request, template_name, context)

    context = {'form': form}
    return render(request, template_name, context)


@login_required
def editarprodutos(request, pk):
    template_name = 'produto/formularios/formulario-editar-produto.html'
    instance = Produto.objects.get(pk=pk)
    form = ProdutoForms(request.POST or None, instance=instance, initial={'usuario':request.user})
    if instance.usuario != request.user:
        raise PermissionError

    if request.method == 'POST':
        if form.is_valid():
            produto = form.save()
            template_name = 'produto/tabela/linhas-tabela-produto.html'
            context = {'object': produto}
            return render(request, template_name, context)

    context = {'form': form, 'object': instance}
    return render(request, template_name, context)


@login_required
def apagarprodutos(request, pk):
    template_name = 'produto/tabela/tabela-produto.html'
    obj = Produto.objects.get(pk=pk)
    if obj.usuario == request.user:
        obj.delete()
    else:
        raise PermissionError
    return render(request, template_name)
