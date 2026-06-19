import json

from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.generic import ListView, DetailView

from fornecedor.models import Fornecedores
from fornecedor.forms import FornecedorForm
from django.contrib.auth.decorators import login_required


class ListaFornecedor(ListView):
    model = Fornecedores
    template_name = 'fornecedor/pagina-inicial-fornecedor.html'

    def get_queryset(self):
        return Fornecedores.objects.filter(usuario=self.request.user)


def _fornecedor_payload(fornecedor):
    meta = fornecedor.cnpj or fornecedor.telefone_contato or fornecedor.telefone_contato_2 or ''
    return {
        'id': fornecedor.pk,
        'text': fornecedor.nome_fornecedor,
        'name': fornecedor.nome_fornecedor,
        'phone': fornecedor.telefone_contato or '',
        'phone_secondary': fornecedor.telefone_contato_2 or '',
        'cpf': fornecedor.cnpj or '',
        'meta': meta,
    }


@login_required
def buscarfornecedores(request):
    termo = request.GET.get('q', '').strip()
    fornecedores = Fornecedores.objects.filter(usuario=request.user)

    if termo:
        fornecedores = fornecedores.filter(
            Q(nome_fornecedor__icontains=termo)
            | Q(cnpj__icontains=termo)
            | Q(telefone_contato__icontains=termo)
            | Q(telefone_contato_2__icontains=termo)
        )

    fornecedores = fornecedores.order_by('nome_fornecedor')[:30]
    return JsonResponse({'results': [_fornecedor_payload(fornecedor) for fornecedor in fornecedores]})



@login_required
def cadastrarfornecedor(request):
    template_name = 'fornecedor/formularios/formulario-cadastrar-fornecedor.html'
    supplier_picker_mode = request.GET.get('picker') == '1' or request.POST.get('supplier_picker') == '1'
    form = FornecedorForm(request.POST or None, initial={'usuario': request.user})

    if request.method == 'POST':
        if form.is_valid():
            fornecedor = form.save(commit=False)
            fornecedor.usuario = request.user
            fornecedor.save()

            if supplier_picker_mode:
                response = HttpResponse('')
                response['HX-Trigger'] = json.dumps({'fornecedorCriado': _fornecedor_payload(fornecedor)})
                return response

            template_name = 'fornecedor/tabela/linhas-tabela-fornecedor.html'

            context = {'object': fornecedor}
            return render(request, template_name, context)

    context = {'form': form, 'supplier_picker_mode': supplier_picker_mode}
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
    



class DetalheFornecedorView(DetailView):
    model = Fornecedores
    template_name = 'fornecedor/off-canvas/detalhe-fornecedor.html'
