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
from django.utils import timezone
from datetime import datetime, timedelta




def inicio_fim_dia(data):
    inicio = timezone.make_aware(
        datetime.combine(data, datetime.min.time())
    )
    fim = timezone.make_aware(
        datetime.combine(data, datetime.max.time())
    )
    return inicio, fim



class ListaVendas(LoginRequiredMixin, ListView):
    model = Vendas
    template_name = "vendas/pagina-inicial-vendas.html"
    context_object_name = "object_list"

    def get_queryset(self):
        qs = (
            Vendas.objects
            .filter(usuario=self.request.user)
            .order_by("-data_criacao")
        )
        
        inicio = self.request.GET.get("inicio")
        fim = self.request.GET.get("fim")
        periodo = self.request.GET.get("periodo")

        ordem = self.request.GET.get("ordem")  # maior | menor


        hoje = timezone.localdate()

        # 🔥 PADRÃO: HOJE
        if not inicio and not fim and not periodo:
            periodo = "hoje"

        # =============================
        # FILTROS POR PERÍODO
        # =============================
        if periodo == "hoje":
            ini, fim_dt = inicio_fim_dia(hoje)
            qs = qs.filter(data_criacao__range=(ini, fim_dt))

        elif periodo == "ontem":
            data = hoje - timedelta(days=1)
            ini, fim_dt = inicio_fim_dia(data)
            qs = qs.filter(data_criacao__range=(ini, fim_dt))

        elif periodo == "7dias":
            ini = timezone.make_aware(
                datetime.combine(hoje - timedelta(days=6), datetime.min.time())
            )
            fim_dt = timezone.make_aware(
                datetime.combine(hoje, datetime.max.time())
            )
            qs = qs.filter(data_criacao__range=(ini, fim_dt))

        elif periodo == "este_mes":
            primeiro_dia = hoje.replace(day=1)
            ini = timezone.make_aware(
                datetime.combine(primeiro_dia, datetime.min.time())
            )
            fim_dt = timezone.make_aware(
                datetime.combine(hoje, datetime.max.time())
            )
            qs = qs.filter(data_criacao__range=(ini, fim_dt))

        elif periodo == "mes_passado":
            primeiro_deste_mes = hoje.replace(day=1)
            ultimo_mes_passado = primeiro_deste_mes - timedelta(days=1)
            primeiro_mes_passado = ultimo_mes_passado.replace(day=1)

            ini = timezone.make_aware(
                datetime.combine(primeiro_mes_passado, datetime.min.time())
            )
            fim_dt = timezone.make_aware(
                datetime.combine(ultimo_mes_passado, datetime.max.time())
            )
            qs = qs.filter(data_criacao__range=(ini, fim_dt))

        elif periodo == "este_ano":
            primeiro_dia = hoje.replace(month=1, day=1)
            ini = timezone.make_aware(
                datetime.combine(primeiro_dia, datetime.min.time())
            )
            fim_dt = timezone.make_aware(
                datetime.combine(hoje, datetime.max.time())
            )
            qs = qs.filter(data_criacao__range=(ini, fim_dt))

        # =============================
        # FILTRO TODAS AS VENDAS
        # =============================
        elif periodo == "todas":
            pass  # não aplica filtro de data


        # =============================
        # FILTRO MANUAL (INÍCIO / FIM)
        # =============================
        else:
            inicio_date = parse_date(inicio) if inicio else None
            fim_date = parse_date(fim) if fim else None

            # 🔹 Apenas uma data preenchida → filtra só aquele dia
            if inicio_date and not fim_date:
                ini, fim_dt = inicio_fim_dia(inicio_date)
                qs = qs.filter(data_criacao__range=(ini, fim_dt))

            elif fim_date and not inicio_date:
                ini, fim_dt = inicio_fim_dia(fim_date)
                qs = qs.filter(data_criacao__range=(ini, fim_dt))

            # 🔹 Intervalo completo
            elif inicio_date and fim_date:
                ini = timezone.make_aware(
                    datetime.combine(inicio_date, datetime.min.time())
                )
                fim_dt = timezone.make_aware(
                    datetime.combine(fim_date, datetime.max.time())
                )
                qs = qs.filter(data_criacao__range=(ini, fim_dt))
        

        # salva para o context
        self._inicio = inicio
        self._fim = fim
        self._periodo = periodo
        self._ordem = ordem
                 # =============================
        # FILTRO MAIOR / MENOR VENDA
        # =============================
        


        return qs


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = context["object_list"]
        
        total_vendas = sum(
            Decimal(v.total() or 0) for v in qs
        )

        total_descontos = sum(
            Decimal(v.desconto or 0) for v in qs
        )

        custo_mercadoria_vendida = sum(
            Decimal(v.custo_total() or 0) for v in qs
        )

        lucro_total = sum(
            (Decimal(v.total() or 0) - Decimal(v.custo_total() or 0) - Decimal(v.desconto or 0))
            for v in qs
        )


        qtd_vendas = qs.count() if hasattr(qs, "count") else len(qs)

        margem = (
            (lucro_total / (total_vendas - total_descontos)) * 100
            if (total_vendas - total_descontos) > 0
            else Decimal("0.00")
        )
    
        context.update({
            "total_vendas": total_vendas,
            "lucro_total": lucro_total,
            "qtd_vendas": qtd_vendas,
            "total_descontos": total_descontos.quantize(Decimal("0.01")),
            "custo_mercadoria_vendida": custo_mercadoria_vendida.quantize(Decimal("0.01")),
            "margem_lucro_total_vendas": margem.quantize(Decimal("0.01")),
            "inicio": self._inicio or "",
            "fim": self._fim or "",
            "periodo": self._periodo or "",
            "ordem": self._ordem or "",
            
           
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
    
    form.items_formset = formset

    if request.method == 'POST':
        if form.is_valid() and formset.is_valid():
            template_name = 'vendas/partials/linha-venda-partial.html'
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
    

    
class TotalVendas(LoginRequiredMixin, ListView):
    model = Vendas
    template_name = "vendas/pagina-inicial-vendas.html"
    context_object_name = "object_list"

    def get_queryset(self):
        qs = (
            Vendas.objects
            .filter(usuario=self.request.user)
            .order_by("-data_criacao")
        )
        
        inicio = self.request.GET.get("inicio")
        fim = self.request.GET.get("fim")
        periodo = self.request.GET.get("periodo")

        ordem = self.request.GET.get("ordem")  # maior | menor


        hoje = timezone.localdate()

        # 🔥 PADRÃO: HOJE
        if not inicio and not fim and not periodo:
            periodo = "hoje"

        # =============================
        # FILTROS POR PERÍODO
        # =============================
        if periodo == "hoje":
            ini, fim_dt = inicio_fim_dia(hoje)
            qs = qs.filter(data_criacao__range=(ini, fim_dt))

        elif periodo == "ontem":
            data = hoje - timedelta(days=1)
            ini, fim_dt = inicio_fim_dia(data)
            qs = qs.filter(data_criacao__range=(ini, fim_dt))

        elif periodo == "7dias":
            ini = timezone.make_aware(
                datetime.combine(hoje - timedelta(days=6), datetime.min.time())
            )
            fim_dt = timezone.make_aware(
                datetime.combine(hoje, datetime.max.time())
            )
            qs = qs.filter(data_criacao__range=(ini, fim_dt))

        elif periodo == "este_mes":
            primeiro_dia = hoje.replace(day=1)
            ini = timezone.make_aware(
                datetime.combine(primeiro_dia, datetime.min.time())
            )
            fim_dt = timezone.make_aware(
                datetime.combine(hoje, datetime.max.time())
            )
            qs = qs.filter(data_criacao__range=(ini, fim_dt))

        elif periodo == "mes_passado":
            primeiro_deste_mes = hoje.replace(day=1)
            ultimo_mes_passado = primeiro_deste_mes - timedelta(days=1)
            primeiro_mes_passado = ultimo_mes_passado.replace(day=1)

            ini = timezone.make_aware(
                datetime.combine(primeiro_mes_passado, datetime.min.time())
            )
            fim_dt = timezone.make_aware(
                datetime.combine(ultimo_mes_passado, datetime.max.time())
            )
            qs = qs.filter(data_criacao__range=(ini, fim_dt))

        elif periodo == "este_ano":
            primeiro_dia = hoje.replace(month=1, day=1)
            ini = timezone.make_aware(
                datetime.combine(primeiro_dia, datetime.min.time())
            )
            fim_dt = timezone.make_aware(
                datetime.combine(hoje, datetime.max.time())
            )
            qs = qs.filter(data_criacao__range=(ini, fim_dt))

        # =============================
        # FILTRO TODAS AS VENDAS
        # =============================
        elif periodo == "todas":
            pass  # não aplica filtro de data


        # =============================
        # FILTRO MANUAL (INÍCIO / FIM)
        # =============================
        else:
            inicio_date = parse_date(inicio) if inicio else None
            fim_date = parse_date(fim) if fim else None

            # 🔹 Apenas uma data preenchida → filtra só aquele dia
            if inicio_date and not fim_date:
                ini, fim_dt = inicio_fim_dia(inicio_date)
                qs = qs.filter(data_criacao__range=(ini, fim_dt))

            elif fim_date and not inicio_date:
                ini, fim_dt = inicio_fim_dia(fim_date)
                qs = qs.filter(data_criacao__range=(ini, fim_dt))

            # 🔹 Intervalo completo
            elif inicio_date and fim_date:
                ini = timezone.make_aware(
                    datetime.combine(inicio_date, datetime.min.time())
                )
                fim_dt = timezone.make_aware(
                    datetime.combine(fim_date, datetime.max.time())
                )
                qs = qs.filter(data_criacao__range=(ini, fim_dt))
        

        # salva para o context
        self._inicio = inicio
        self._fim = fim
        self._periodo = periodo
        self._ordem = ordem
                 # =============================
        # FILTRO MAIOR / MENOR VENDA
        # =============================
        


        return qs


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = context["object_list"]
        
        total_vendas = sum(
            Decimal(v.total() or 0) for v in qs
        )

        total_sem_dessconto = sum(
            Decimal(v.total_sem_desconto() or 0) for v in qs
        )

        total_descontos = sum(
            Decimal(v.desconto or 0) for v in qs
        )

        custo_mercadoria_vendida = sum(
            Decimal(v.custo_total() or 0) for v in qs
        )

        cmv = sum(
            Decimal(v.cmv() or 0) for v in qs
        )

        lucro_total = sum(
            (Decimal(v.total() or 0) - Decimal(v.custo_total() or 0) - Decimal(v.desconto or 0))
            for v in qs
        )


        qtd_vendas = qs.count() if hasattr(qs, "count") else len(qs)

        margem = (
            (lucro_total / (total_vendas - total_descontos)) * 100
            if (total_vendas - total_descontos) > 0
            else Decimal("0.00")
        )
    
        context.update({
            "total_vendas": total_vendas,
            "total_sem_desconto": total_sem_dessconto,
            "lucro_total": lucro_total,
            "qtd_vendas": qtd_vendas,
            "total_descontos": total_descontos.quantize(Decimal("0.01")),
            "custo_mercadoria_vendida": custo_mercadoria_vendida.quantize(Decimal("0.01")),
            "cmv": cmv,
            "margem_lucro_total_vendas": margem.quantize(Decimal("0.01")),
            "inicio": self._inicio or "",
            "fim": self._fim or "",
            "periodo": self._periodo or "",
            "ordem": self._ordem or "",
            
           
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

def produto_preco(request):
    produto_id = request.GET.get('produto_id')

    try:
        produto = Produto.objects.get(pk=produto_id)
        return JsonResponse({'preco': produto.preco_venda})
    except Produto.DoesNotExist:
        return JsonResponse({'preco': '0.00'})