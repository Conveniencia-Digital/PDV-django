from decimal import Decimal
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotAllowed, JsonResponse
from django.shortcuts import get_object_or_404, render
from venda.forms import ItemsVendaForm, VendasItemsFormset, VendasForm
from django.views.generic import ListView, DetailView
from produto.models import Produto
from venda.services import aplicar_filtro_periodo_vendas, build_vendas_dashboard
from venda.models import Vendas, ItemsVenda, VendasSubmissionToken
from django.contrib.auth.decorators import login_required
from django.utils.dateparse import parse_date
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from datetime import datetime, timedelta

from financeiro.card_fees import (
    apply_card_fee_to_transaction,
    calculate_card_fee,
    preview_card_fee,
    sync_card_fee_expense,
)



def inicio_fim_dia(data):
    inicio = timezone.make_aware(
        datetime.combine(data, datetime.min.time())
    )
    fim = timezone.make_aware(
        datetime.combine(data, datetime.max.time())
    )
    return inicio, fim


def _criar_submission_token(user, finalidade):
    return VendasSubmissionToken.objects.create(
        usuario=user,
        finalidade=finalidade,
        token=uuid4().hex,
    ).token


def _consumir_submission_token(user, finalidade, token):
    if not token:
        return False
    token_obj = (
        VendasSubmissionToken.objects
        .select_for_update()
        .filter(usuario=user, finalidade=finalidade, token=token, usado_em__isnull=True)
        .first()
    )
    if not token_obj:
        return False
    token_obj.usado_em = timezone.now()
    token_obj.save(update_fields=['usado_em'])
    return True


def _base_vendas_queryset(user):
    return (
        Vendas.objects
        .filter(usuario=user)
        .select_related("cliente", "vendedor", "card_machine")
        .prefetch_related("vendas_items__produto")
        .order_by("-data_criacao")
    )


def _dashboard_params_from_request(request):
    source = request.POST if request.method == 'POST' else request.GET
    params = {}
    periodo = source.get('dashboard_periodo') or source.get('periodo')
    inicio = source.get('dashboard_inicio') or source.get('inicio')
    fim = source.get('dashboard_fim') or source.get('fim')

    if periodo:
        params['periodo'] = periodo
    if inicio:
        params['inicio'] = inicio
    if fim:
        params['fim'] = fim
    return params


def _dashboard_form_context(request):
    params = _dashboard_params_from_request(request)
    return {
        'dashboard_periodo': params.get('periodo', ''),
        'dashboard_inicio': params.get('inicio', ''),
        'dashboard_fim': params.get('fim', ''),
    }


def _vendas_dashboard_context(user, params):
    qs = _base_vendas_queryset(user)
    object_list, inicio, fim, periodo = aplicar_filtro_periodo_vendas(qs, params)
    context = {'object_list': object_list}
    context.update(build_vendas_dashboard(user, params))
    context.update({
        'inicio': inicio or '',
        'fim': fim or '',
        'periodo': periodo or '',
        'ordem': params.get('ordem', ''),
    })
    return context


def _render_dashboard_update(request, trigger=None):
    context = _vendas_dashboard_context(request.user, _dashboard_params_from_request(request))
    response = render(request, 'vendas/bloco-dados.html', context)
    response['HX-Retarget'] = '#bloco-dados'
    response['HX-Reswap'] = 'outerHTML'
    if trigger:
        response['HX-Trigger'] = trigger
    return response


def _base_venda_formset(form, formset):
    total = Decimal("0.00")
    for item in formset.cleaned_data:
        preco = item.get('preco') or Decimal("0.00")
        quantidade = item.get('quantidade') or 0
        total += preco * quantidade

    desconto = form.cleaned_data.get('desconto') or Decimal("0.00")
    return max(total - desconto, Decimal("0.00"))


def _add_card_fee_error(form, error):
    messages = getattr(error, 'messages', None) or [str(error)]
    for message in messages:
        form.add_error(None, message)


def _prepare_venda_for_save(user, form, formset):
    venda = form.save(commit=False)
    venda.usuario = user
    base_amount = _base_venda_formset(form, formset)

    calculation = calculate_card_fee(
        user=user,
        payment_method=venda.forma_pagamento,
        card_machine=venda.card_machine,
        installments=venda.card_installments,
        base_amount=base_amount,
        pass_fee_to_customer=venda.pass_card_fee_to_customer,
    )
    apply_card_fee_to_transaction(venda, calculation)
    return venda


def _save_venda_with_items(venda, formset):
    venda.save()
    formset.instance = venda
    items_venda = formset.save()
    sync_card_fee_expense(
        venda,
        "venda_card_fee",
        "Venda",
        should_create=venda.status == Vendas.ENTREGUE,
    )
    return items_venda



class ListaVendas(LoginRequiredMixin, ListView):
    model = Vendas
    template_name = "vendas/pagina-inicial-vendas.html"
    context_object_name = "object_list"

    def get_queryset(self):
        qs = _base_vendas_queryset(self.request.user)
        qs, self._inicio, self._fim, self._periodo = aplicar_filtro_periodo_vendas(qs, self.request.GET)
        self._ordem = self.request.GET.get("ordem")
        return qs


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(build_vendas_dashboard(self.request.user, self.request.GET))
        context["ordem"] = self._ordem or ""
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
    submission_token = request.POST.get('submission_token') or _criar_submission_token(request.user, 'venda')
    
    form.items_formset = formset

    if request.method == 'POST':
        if form.is_valid() and formset.is_valid():
            try:
                vendas = _prepare_venda_for_save(request.user, form, formset)
            except ValidationError as error:
                _add_card_fee_error(form, error)
            else:
                with transaction.atomic():
                    if not _consumir_submission_token(request.user, 'venda', submission_token):
                        response = HttpResponse('Esta venda já foi processada.', status=409)
                        response['HX-Trigger'] = 'vendaDuplicada'
                        return response
                    _save_venda_with_items(vendas, formset)
                return _render_dashboard_update(request, 'vendaSalva')

    context = {'form': form, 'formset': formset, 'submission_token': submission_token}
    context.update(_dashboard_form_context(request))
    return render(request, template_name, context)


@login_required
def buscarpreco(request):
    template_name = 'vendas/formularios/preco-produto.html'
    produto_pk = None
    item_index = '0'

    for key, value in request.GET.items():
        if key.startswith('items-') and key.endswith('-produto'):
            parts = key.split('-')
            if len(parts) >= 3:
                item_index = parts[1]
            produto_pk = value
            break
        if key == 'produto':
            produto_pk = value

    if not produto_pk:
        return HttpResponseBadRequest('Produto não informado')

    produto = get_object_or_404(Produto, pk=produto_pk, usuario=request.user)
    context = {'produto': produto, 'item': item_index}
    return render(request, template_name, context)



@login_required
def addform(request):
    template_name = 'vendas/formularios/addform.html'
    form = ItemsVendaForm(user=request.user)
    context = {'itemsvendaform': form}
    return render(request, template_name, context)



@login_required
def apagaritemvenda(request, pk):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    item_venda = get_object_or_404(ItemsVenda.objects.select_related('vendas'), pk=pk)
    if item_venda.vendas_id and item_venda.vendas.usuario_id != request.user.id:
        raise PermissionError
    item_venda.delete()
    return HttpResponse('')


class DetalheVendas(DetailView):
    template_name = 'vendas/detalhe-venda.html'
    model = Vendas

    def get_queryset(self):
        return Vendas.objects.filter(usuario=self.request.user)


@login_required
def editarvendas(request, pk):
    template_name = 'vendas/formularios/formulario-editar-vendas.html'
    venda_instance = get_object_or_404(Vendas, pk=pk, usuario=request.user)

    form = VendasForm(request.POST or None, user=request.user, initial={'usuario': request.user}, instance=venda_instance, prefix='main')
    formset = VendasItemsFormset(request.POST or None, form_kwargs={'user': request.user}, instance=venda_instance, prefix='items')
    
    if request.method == 'POST':
        if form.is_valid() and formset.is_valid():
            try:
                vendas = _prepare_venda_for_save(request.user, form, formset)
            except ValidationError as error:
                _add_card_fee_error(form, error)
            else:
                with transaction.atomic():
                    _save_venda_with_items(vendas, formset)
                return _render_dashboard_update(request, 'vendaSalva')
        else:
            print(form.errors)
            print(formset.errors)
   
    context = {'object':venda_instance, 'form': form, 'formset': formset}
    context.update(_dashboard_form_context(request))
    return render(request, template_name, context)


@login_required
def apagarvendas(request, pk):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    venda = get_object_or_404(Vendas.objects.filter(usuario=request.user), pk=pk)
    with transaction.atomic():
        for item in venda.vendas_items.select_related('produto').all():
            item.delete()
        venda.delete()
    return _render_dashboard_update(request, 'vendaExcluida')



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
        return JsonResponse({'preco': produto.preco})
    except Produto.DoesNotExist:
        return JsonResponse({'preco': '0.00'})


@login_required
def previewtaxacartaovenda(request):
    forma_pagamento = request.GET.get('forma_pagamento', '')
    base_amount = request.GET.get('base_amount') or 0
    pass_fee = request.GET.get('pass_fee') in ('1', 'true', 'on', 'True')
    installments = request.GET.get('installments') or None
    machine_pk = request.GET.get('card_machine') or None

    preview = preview_card_fee(request.user, forma_pagamento, machine_pk, installments, base_amount, pass_fee)
    return JsonResponse(preview['payload'], status=preview['status'])
