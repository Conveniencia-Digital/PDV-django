from django.shortcuts import render
from venda.forms import ItemsVendaForm, VendasItemsFormset, VendasForm
from django.views.generic import ListView, DetailView
from produto.models import Produto
from venda.models import Vendas, ItemsVenda
from django.contrib.auth.decorators import login_required
from django.utils.dateparse import parse_date
from django.utils.timezone import now
from datetime import timedelta
from decimal import Decimal
from django.contrib.auth.mixins import LoginRequiredMixin


class ListaVendas(LoginRequiredMixin, ListView):
    model = Vendas
    template_name = "vendas/pagina-inicial-vendas.html"
    context_object_name = "object_list"

    def get_queryset(self):
        qs = Vendas.objects.filter(usuario=self.request.user).order_by('-data_criacao')

        inicio = self.request.GET.get("inicio")
        fim = self.request.GET.get("fim")
        periodo = self.request.GET.get("periodo")
        hoje = now().date()
        

        # 👉 FILTRO PADRÃO: HOJE
        if not inicio and not fim and not periodo:
            periodo = "hoje"

        if periodo:
            if periodo == "hoje":
                qs = qs.filter(data_criacao__date=hoje)
            elif periodo == "ontem":
                qs = qs.filter(data_criacao__date=hoje - timedelta(days=1))
            elif periodo == "7dias":
                qs = qs.filter(data_criacao__date__gte=hoje - timedelta(days=7))
            elif periodo == "este_mes":
                qs = qs.filter(
                    data_criacao__date__gte=hoje.replace(day=1),
                    data_criacao__date__lte=hoje
                )
            elif periodo == "mes_passado":
                primeiro_deste_mes = hoje.replace(day=1)
                ultimo_mes_passado = primeiro_deste_mes - timedelta(days=1)
                primeiro_mes_passado = ultimo_mes_passado.replace(day=1)
                qs = qs.filter(
                    data_criacao__date__gte=primeiro_mes_passado,
                    data_criacao__date__lte=ultimo_mes_passado
                )
            elif periodo == "este_ano":
                qs = qs.filter(data_criacao__year=hoje.year)
        else:
            if inicio:
                inicio_date = parse_date(inicio)
                if inicio_date:
                    qs = qs.filter(data_criacao__date__gte=inicio_date)
            if fim:
                fim_date = parse_date(fim)
                if fim_date:
                    qs = qs.filter(data_criacao__date__lte=fim_date)
        context = {
            "inicio": inicio,
            "fim": fim,
            "periodo": periodo,
            }
        
        return qs
        
        


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = context["object_list"]

        total_vendas = sum(v.total() or 0 for v in qs)
        lucro_total = sum(v.lucro_total() or 0 for v in qs)
        qtd_vendas = qs.count()

        if total_vendas == 0:
            margem = Decimal("0.00")
        else:
            margem = (lucro_total / total_vendas) * 100

        context.update({
            
            "total_vendas": total_vendas,
            "lucro_total": lucro_total,
            "qtd_vendas": qtd_vendas,
            "margem_lucro_total_vendas": margem.quantize(Decimal("0.01")),
            "inicio": self.request.GET.get("inicio", ""),
            "fim": self.request.GET.get("fim", ""),
            "periodo": self.request.GET.get("periodo", ""),
            
        })

        return context

    def render_to_response(self, context, **response_kwargs):
        if self.request.htmx:
            return self.response_class(
                request=self.request,
                template="vendas/bloco-dados.html",
                context=context,
                **response_kwargs
            )
        return super().render_to_response(context, **response_kwargs)


@login_required
def cadastrarvendas(request):
    template_name = 'vendas/formularios/formulario-cadastrar-vendas.html'
    venda_instance = Vendas()

    form = VendasForm(request.POST or None, user=request.user, initial={'usuario': request.user}, instance=venda_instance, prefix='main')
    formset = VendasItemsFormset(request.POST or None, instance=venda_instance, prefix='items', form_kwargs={'user': request.user})
    

    if request.method == 'POST':
        if form.is_valid() and formset.is_valid():
            template_name = 'vendas/tabela/linhas-tabela-vendas.html'
            vendas = form.save()
            items_venda = formset.save()
                   
            context = {'object': vendas, 'items': items_venda}
            return render(request, template_name, context)

    context = {'form': form, 'formset': formset}
    return render(request, template_name, context)


@login_required
def buscarpreco(request):
    template_name = 'vendas/formularios/preco-produto.html'
    url = request.get_full_path()
    print('url', url)
    print(url.split('-'))
    print('list', list(request.GET.values()))
    lista = list(request.GET.values())
    produto_pk = 0
    for i in lista:
        produto_pk = i
    

    produto = Produto.objects.get(pk=produto_pk)
    context = {'produto': produto}
    return render(request, template_name, context)



@login_required
def addform(request):
    template_name = 'vendas/formularios/addform.html'
    form = ItemsVendaForm(user=request.user)
    context = {'itemsvendaform': form}
    return render(request, template_name, context)



@login_required
def apagaritemvenda(request, pk):
    item_orcamento = ItemsVenda.objects.get(pk=pk)
    if item_orcamento.usuario == request.user:
        item_orcamento.delete()
        return None
    else:
        raise PermissionError


class DetalheVendas(DetailView):
    template_name = 'vendas/detalhe-venda.html'
    model = Vendas

    def get_queryset(self):
        return Vendas.objects.filter(usuario=self.request.user)


@login_required
def editarvendas(request, pk):
    template_name = 'vendas/formularios/formulario-editar-vendas.html'
    venda_instance = Vendas.objects.get(pk=pk)

    form = VendasForm(request.POST or None, user=request.user, initial={'usuario': request.user}, instance=venda_instance, prefix='main')
    formset = VendasItemsFormset(request.POST or None, form_kwargs={'user': request.user}, instance=venda_instance, prefix='items')

    if venda_instance.usuario != request.user:
        raise PermissionError
    
    if request.method == 'POST':
        if form.is_valid() and formset.is_valid():
            
            template_name = 'vendas/tabela/linhas-tabela-vendas.html'
            vendas = form.save()
            items_venda = formset.save()
            context = {'object': vendas, 'items': items_venda}
            return render(request, template_name, context)
        else:
            print(form.errors)
            print(formset.errors)
   
    context = {'object':venda_instance, 'form': form, 'formset': formset}
    return render(request, template_name, context)



def valor_total_vendas(request):
    template_name = 'vendas/relatorios/relatorio-venda.html'
    vendas = Vendas.objects.filter(usuario=request.user).count()
    valor_total = sum(venda.total() for venda in Vendas.objects.filter(usuario=request.user))
    context = {'vendas': vendas, 'valor_total': valor_total}
    return render(request, template_name, context)


class RelatorioLucro(DetailView):
    template_name = 'vendas/relatorios/relatorio-lucro.html'
    model = Vendas

    def get_queryset(self):
        return Vendas.objects.filter(usuario=self.request.user)
    

    


