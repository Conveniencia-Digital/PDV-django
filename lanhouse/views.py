from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.generic import ListView

from lanhouse.forms import ItemsLanhouseForm, LanhouseForm, LanhouseFormset, LanhouseServicoForm
from lanhouse.models import LanhouseModel, LanhouseServico


class ListaLanhouse(ListView):
    model = LanhouseModel
    template_name = 'lanhouse/pagina-inicial-lanhouse.html'

    def get_queryset(self):
        return LanhouseModel.objects.filter(usuario=self.request.user)


@login_required
def cadastrarlanhouse(request):
    template_name = 'lanhouse/formularios/formulario-cadastrar-lanhouse.html'
    lanhouse_instance = LanhouseModel()
    form = LanhouseForm(request.POST or None, user=request.user, initial={
                        'usuario': request.user}, instance=lanhouse_instance, prefix='main')
    formset = LanhouseFormset(request.POST or None, instance=lanhouse_instance,
                              prefix='items', form_kwargs={'user': request.user})

    if request.method == 'POST':
        if form.is_valid() and formset.is_valid():
            lanhouse = form.save()
            items_lanhouse = formset.save()
            template_name = 'lanhouse/tabela/linha-tabela-lanhouse.html'
            context = {'object': lanhouse, 'items': items_lanhouse}
            return render(request, template_name, context)

    context = {'form': form, 'formset': formset}
    return render(request, template_name, context)


@login_required
def precoservicolanhouse(request):
    template_name = 'lanhouse/formularios/preco-servico-lanhouse.html'
    url = request.get_full_path()
    print('url', url)
    print(url.split('-'))
    print('list', list(request.GET.values()))
    lista = list(request.GET.values())
    servico_lanhouse_pk = 0
    for i in lista:
        servico_lanhouse_pk = i

    servico = LanhouseServico.objects.get(pk=servico_lanhouse_pk)
    context = {'servico': servico}
    return render(request, template_name, context)


@login_required
def cadastrarservicolanhouse(request):
    template_name = 'lanhouse/formularios/formulario-cadastrar-servico-lanhouse.html'
    form = LanhouseServicoForm(request.POST or None, initial={'usuario': request.user})

    if request.method == 'POST':
        if form.is_valid():
            servico = form.save()
            template_name = 'lanhouse/tabela/linhas-tabela-servico.html'
            context = {'object': servico}
            return render(request, template_name, context)

    context = {'form': form}
    return render(request, template_name, context)


@login_required
def editarservicolanhouse(request, pk):
    template_name = 'lanhouse/formularios/formulario-editar-servico-lanhouse.html'
    instance = LanhouseServico.objects.get(pk=pk)
    form = LanhouseServicoForm(request.POST or None, instance=instance, initial={'usuario': request.user})

    if request.method == 'POST':
        if form.is_valid():
            servico = form.save()
            template_name = 'lanhouse/tabela/linhas-tabela-servico.html'
            context = {'object': servico}
            return render(request, template_name, context)

    context = {'form': form, 'object': instance}
    return render(request, template_name, context)


@login_required
def apagarservicolanhouse(request, pk):
    template_name = 'lanhouse/tabela/tabela-servico-lanhouse.html'
    servico = LanhouseServico.objects.get(pk=pk)
    servico.delete()
    return render(request, template_name)


@login_required
def additemlanhouse(request):
    template_name = 'lanhouse/formularios/add-item-lanhouse.html'
    form = ItemsLanhouseForm(user=request.user)
    context = {'itemslanhouse': form}
    return render(request, template_name, context)


class ListaServicoLanhouse(ListView):
    model = LanhouseServico
    template_name = 'lanhouse/lista-servico-lanhouse.html'

    def get_queryset(self):
        return LanhouseServico.objects.filter(usuario=self.request.user)


def relatorio_lanhouse(request):
    template_name = 'lanhouse/relatorios/relatorio-lanhouse.html'
    qtd_lanhouse = LanhouseModel.objects.filter(usuario=request.user).count()
    valor_total = sum(qtd.total() for qtd in LanhouseModel.objects.filter(usuario=request.user))
    context = {'qtd_lanhouse': qtd_lanhouse, 'valor_total': valor_total}
    return render(request, template_name, context)
