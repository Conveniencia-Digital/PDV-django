from django.shortcuts import render
from django.views.generic import ListView

from fornecedor.models import Fornecedores
from fornecedor.forms import FornecedorForm
from django.contrib.auth.decorators import login_required


class ListaFornecedor(ListView):
    model = Fornecedores
    template_name = 'fornecedor/pagina-inicial-fornecedor.html'

    def get_queryset(self):
        return Fornecedores.objects.filter(usuario=self.request.user)



@login_required
def cadastrarfornecedor(request):
    template_name = 'fornecedor/formularios/formulario-cadastrar-fornecedor.html'
    form = FornecedorForm(request.POST or None, initial={'usuario': request.user})

    if request.method == 'POST':
        if form.is_valid():
            fornecedor = form.save()
            template_name = 'fornecedor/tabela/linhas-tabela-fornecedor.html'

            context = {'object': fornecedor}
            return render(request, template_name, context)

    context = {'form': form}
    return render(request, template_name, context)



@login_required
def editarfornecedor(request, pk):
    template_name = 'fornecedor/formularios/formulario-editar-fornecedor.html'
    instance = Fornecedores.objects.get(pk=pk)
    form = FornecedorForm(request.POST or None, instance=instance, initial={'usuario':request.user})
    
    if instance.usuario != request.user:
        raise PermissionError

    if request.method == 'POST':
        if form.is_valid():
            fornecedor = form.save()
            template_name = 'fornecedor/tabela/linhas-tabela-fornecedor.html'
            context = {'object': fornecedor}

            return render(request, template_name, context)

    context = {'form': form, 'object': instance}
    return render(request, template_name, context)



@login_required
def apagarfornecedor(request, pk):
    template_name = 'fornecedor/tabela/tabela-fornecedor.html'
    obj = Fornecedores.objects.get(pk=pk)
    if obj.usuario == request.user:
        obj.delete()
    else:
        raise PermissionError
    return render(request, template_name)




@login_required
def total_fornecedor(request):
    template_name = 'fornecedor/informacao-fornecedor.html'
    total_fornecedor =  Fornecedores.objects.count()
    context = {'total_fornecedor': total_fornecedor}
    return render(request, template_name, context)
    