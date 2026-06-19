from decimal import Decimal

from django import forms
from produto.models import CategoriaProduto, Produto, ensure_default_categories
from fornecedor.models import Fornecedores


class ProdutoForms(forms.ModelForm):

    class Meta:
        model = Produto
        fields = (
            'usuario',
            'nome_produto',
            'categoria',
            'quantidade',
            'codigo_de_barras',
            'preco_de_custo',
            'margem_de_lucro',
            'preco',
            'forma_pagamento',
            'fornecedor',
            'observacao',
            'data_vencimento',
            'qtd_parcela',
            'valor_entrada',
        )

        widgets = {
            'observacao': forms.Textarea(attrs={'rows': 2}),
            
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(ProdutoForms, self).__init__(*args, **kwargs)
        user = user or getattr(self.instance, 'usuario', None)
        ensure_default_categories(user)

        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
        
        self.fields['usuario'].widget = forms.HiddenInput()
        self.fields['categoria'].queryset = CategoriaProduto.objects.filter(usuario=user).order_by('nome')
        self.fields['fornecedor'].queryset = Fornecedores.objects.filter(usuario=user)

        if (
            self.instance
            and self.instance.pk
            and not self.instance.categoria_id
            and self.instance.categoria_produtos
        ):
            categoria = self.fields['categoria'].queryset.filter(nome=self.instance.categoria_produtos).first()
            if categoria:
                self.initial['categoria'] = categoria.pk

    def clean(self):
        cleaned_data = super().clean()
        forma_pagamento = cleaned_data.get('forma_pagamento')
        preco_de_custo = cleaned_data.get('preco_de_custo')
        quantidade = cleaned_data.get('quantidade')
        valor_entrada = cleaned_data.get('valor_entrada')

        if forma_pagamento != Produto.FIADO:
            cleaned_data['valor_entrada'] = None
            cleaned_data['qtd_parcela'] = None
            cleaned_data['data_vencimento'] = None
            return cleaned_data

        if preco_de_custo is None or quantidade is None:
            return cleaned_data

        custo_total = preco_de_custo * quantidade
        entrada = valor_entrada or Decimal('0.00')
        cleaned_data['valor_entrada'] = entrada

        if entrada < 0:
            self.add_error('valor_entrada', 'O valor de entrada não pode ser negativo.')
        elif entrada > custo_total:
            self.add_error('valor_entrada', 'O valor de entrada não pode ser maior que o custo total do estoque.')

        return cleaned_data

    def save(self, commit=True):
        produto = super().save(commit=False)
        produto.categoria_produtos = produto.categoria.nome if produto.categoria_id else None
        if commit:
            produto.save()
            self.save_m2m()
        return produto


class CategoriaProdutoForm(forms.ModelForm):
    class Meta:
        model = CategoriaProduto
        fields = ('usuario', 'nome')

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['usuario'].widget = forms.HiddenInput()
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    def clean_nome(self):
        nome = (self.cleaned_data.get('nome') or '').strip()
        if not nome:
            raise forms.ValidationError('Informe o nome da categoria.')

        if self.user and CategoriaProduto.objects.filter(usuario=self.user, nome__iexact=nome).exists():
            raise forms.ValidationError('Esta categoria já está cadastrada.')

        return nome

    def save(self, commit=True):
        categoria = super().save(commit=False)
        if self.user:
            categoria.usuario = self.user
        if commit:
            categoria.save()
        return categoria
