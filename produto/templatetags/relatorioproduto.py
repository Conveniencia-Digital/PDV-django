from django import template

from produto.models import Produto

register =  template.Library()



@register.simple_tag
def total_produtos(request):
    valor_total = sum(produto.vendatotal() for produto in Produto.objects.filter(usuario=request.user))
    return valor_total


@register.simple_tag
def lucro_total_produtos(request):
    valor_total_lucro = sum(produto.lucrototal() for produto in Produto.objects.filter(usuario=request.user))
    return valor_total_lucro

@register.simple_tag
def quantidade_produtos(request):
    qtd_produtos = sum(produto.qtdproduto() for produto in Produto.objects.filter(usuario=request.user))
    return qtd_produtos

@register.simple_tag
def custo_total_produto(request):
    custo_total = sum(produto.precototal() for produto in Produto.objects.filter(usuario=request.user))
    return custo_total

@register.simple_tag
def margem_de_lucro_produto(request):
    produtos = Produto.objects.filter(usuario=request.user)
    total_lucro = sum(p.lucrototal() for p in produtos)
    total_venda = sum(p.vendatotal() for p in produtos)

    if total_venda == 0:
        return 0
    
    margem_percentual = (total_lucro / total_venda) * 100
    return round(margem_percentual, 2)



