import json

from django.shortcuts import render
from django.views.generic import ListView, DetailView
from django.db.models import Q
from django.http import HttpResponse, JsonResponse

from produto.forms import CategoriaProdutoForm, ProdutoForms
from produto.models import CategoriaProduto, Produto, ensure_default_categories
from produto.services import build_produto_dashboard
from django.contrib.auth.decorators import login_required

class ListaProduto(ListView):
    model = Produto
    template_name = 'produto/pagina-inicial-produto.html'

    def get_template_names(self):
        if self.request.headers.get('HX-Request') == 'true':
            return ['produto/bloco-dados.html']
        return [self.template_name]

    def get_queryset(self):
        ensure_default_categories(self.request.user)
        return Produto.objects.filter(usuario=self.request.user).select_related('categoria').order_by('-data_criacao')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(build_produto_dashboard(self.request.user))
        return context


def _categoria_payload(categoria):
    return {
        'id': categoria.pk,
        'text': categoria.nome,
        'name': categoria.nome,
        'meta': 'Categoria de produto',
    }


@login_required
def buscarprodutos(request):
    termo = request.GET.get('q', '').strip()
    produtos = Produto.objects.filter(usuario=request.user, quantidade__gt=0).select_related('categoria')

    if termo:
        produtos = produtos.filter(
            Q(nome_produto__icontains=termo)
            | Q(categoria_produtos__icontains=termo)
            | Q(categoria__nome__icontains=termo)
            | Q(codigo_de_barras__icontains=termo)
        )

    produtos = produtos.order_by('nome_produto')[:30]
    return JsonResponse({
        'results': [
            {
                'id': produto.pk,
                'text': produto.nome_produto,
                'name': produto.nome_produto,
                'price': str(produto.preco or 0),
                'cost': str(produto.preco_de_custo or 0),
                'meta': f'Estoque: {produto.quantidade} | R$ {produto.preco}',
            }
            for produto in produtos
        ]
    })


@login_required
def buscarcategoriasproduto(request):
    ensure_default_categories(request.user)
    termo = request.GET.get('q', '').strip()
    categorias = CategoriaProduto.objects.filter(usuario=request.user)

    if termo:
        categorias = categorias.filter(nome__icontains=termo)

    categorias = categorias.order_by('nome')[:30]
    return JsonResponse({'results': [_categoria_payload(categoria) for categoria in categorias]})


@login_required
def criarcategoriaproduto(request):
    template_name = 'produto/formularios/formulario-cadastrar-categoria-produto.html'
    picker_mode = request.GET.get('picker') == '1' or request.POST.get('category_picker') == '1'
    form = CategoriaProdutoForm(request.POST or None, initial={'usuario': request.user}, user=request.user)

    if request.method == 'POST':
        if form.is_valid():
            categoria = form.save()

            if picker_mode:
                response = HttpResponse('')
                response['HX-Trigger'] = json.dumps({'produtoCategoriaCriada': _categoria_payload(categoria)})
                return response

            response = HttpResponse('<div class="alert alert-success">Categoria cadastrada com sucesso.</div>')
            response['HX-Trigger'] = json.dumps({'produtoCategoriaCriada': _categoria_payload(categoria)})
            return response

    context = {'form': form, 'category_picker_mode': picker_mode}
    return render(request, template_name, context)


@login_required
def criarprodutos(request):
    template_name = 'produto/formularios/formulario-cadastrar-produto.html'
    form = ProdutoForms(request.POST or None, initial={'usuario': request.user}, user=request.user)
    

    if request.method == 'POST':
        if form.is_valid():
            produto = form.save()
            template_name = 'produto/tabela/linhas-tabela-produto.html'

            context = {'object': produto}
            response = render(request, template_name, context)
            response['HX-Retarget'] = '#produto-Tbody'
            response['HX-Reswap'] = 'afterbegin'
            response['HX-Trigger'] = 'produtoSalvo'
            return response

    context = {'form': form}
    return render(request, template_name, context)


@login_required
def editarprodutos(request, pk):
    template_name = 'produto/formularios/formulario-editar-produto.html'
    instance = Produto.objects.get(pk=pk)
    form = ProdutoForms(request.POST or None, instance=instance, initial={'usuario':request.user}, user=request.user)
    if instance.usuario != request.user:
        raise PermissionError

    if request.method == 'POST':
        if form.is_valid():
            produto = form.save()
            template_name = 'produto/tabela/linhas-tabela-produto.html'
            context = {'object': produto}
            response = render(request, template_name, context)
            response['HX-Retarget'] = f'#trProduto{produto.pk}'
            response['HX-Reswap'] = 'outerHTML'
            response['HX-Trigger'] = 'produtoEditado'
            return response

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
    response = render(request, template_name)
    response['HX-Trigger'] = 'produtoExcluido'
    return response


class DetalheProduto(DetailView):
    model = Produto
    template_name = 'produto/detalhes/detalhe-produtos.html'
