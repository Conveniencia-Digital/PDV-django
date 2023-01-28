from django.shortcuts import render
from django.views.generic import ListView, DetailView
from orcamento.models import Orcamento, ItemsOrcamento
from orcamento.forms import OrcamentoForms, ItemsOrcamentoForms, ItemsOrcamentoFormset
from peca.models import Pecas
from django.contrib.auth.decorators import login_required


class ListaOrcamento(ListView):
    template_name = 'orcamento/pagina-inicial-orcamento.html'
    model = Orcamento

    def get_queryset(self):
        return Orcamento.objects.filter(usuario=self.request.user)



@login_required
def cadastrarorcamento(request):
    template_name = 'orcamento/formularios/formulario-cadastrar-orcamento.html'
    orcamento_instance = Orcamento()

    form = OrcamentoForms(request.POST or None, usuario=request.user, initial={'usuario': request.user}, instance=orcamento_instance, prefix='main')
    formset = ItemsOrcamentoFormset(request.POST or None, instance=orcamento_instance, prefix='items', form_kwargs={'usuario': request.user})


    if request.method == 'POST':
        if form.is_valid() and formset.is_valid():
            template_name = 'orcamento/tabela/linhas-tabela-orcamento.html'
            orcamento = form.save()
            items_orcamento = formset.save()
            context = {'object': orcamento, 'items': items_orcamento}
            return render(request, template_name, context)

    context = {'form': form, 'formset': formset}
    return render(request, template_name, context)

    
@login_required
def editarorcamento(request, pk):
    template_name = 'orcamento/formularios/formulario-editar-orcamento.html'
    orcamento_instance = Orcamento.objects.get(pk=pk)

    form = OrcamentoForms(request.POST or None, usuario=request.user, initial={'usuario': request.user}, instance=orcamento_instance, prefix='main')
    formset = ItemsOrcamentoFormset(request.POST or None, instance=orcamento_instance, prefix='items', form_kwargs={'usuario': request.user})

    if orcamento_instance.usuario != request.user:
        raise PermissionError

    if request.method == 'POST':
        if form.is_valid() and formset.is_valid():
            template_name = 'orcamento/tabela/linhas-tabela-orcamento.html'
            orcamento = form.save()
            items_orcamento = formset.save()
            context = {'object': orcamento, 'items': items_orcamento}
            return render(request, template_name, context)
    
    context = {'object': orcamento_instance, 'form': form, 'formset': formset}
    return render(request, template_name, context)


@login_required
def adicionarlinhas(request):
    template_name = 'orcamento/formularios/linhas-formulario-orcamento.html'
    form = ItemsOrcamentoForms(usuario=request.user)
    context = {'items_orcamento_form': form}
    return render(request, template_name, context)



@login_required
def adicionarlinhaservico(request):
    template_name = 'orcamento/formularios/linha-servico-orcamento.html'
    form = ItemsOrcamentoForms(usuario=request.user)
    context = {'items_orcamento_form': form}
    return render(request, template_name, context)



@login_required
def preco_peca(request):
    template_name = 'orcamento/formularios/preco-peca.html'
    url = request.get_full_path()
    print('url', url)
    print(url.split('-'))
    print('list', list(request.GET.values()))
    lista = list(request.GET.values())
    peca_pk = 0
    for i in lista:
        peca_pk = i
    peca = Pecas.objects.get(pk=peca_pk)
    context = {'peca': peca}
    return render(request, template_name, context)



@login_required
def apagaritemorcamento(pk):
    item_orcamento = ItemsOrcamento.objects.get(pk=pk)
    item_orcamento.delete()
    return None


class DetalheOrcamento(DetailView):
    model = Orcamento
    template_name= 'orcamento/detalhe-orcamento.html'

    def get_queryset(self):
        return Orcamento.objects.filter(usuario=self.request.user)
    