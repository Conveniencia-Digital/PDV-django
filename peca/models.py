from django.db import models


class Pecas(models.Model):
    TELAS = 'FN'
    CONECTORES = 'CB'
    BOTOES = 'CL'
    CARCACAS = 'IP'
    BATERIAS = 'CR'
    PLACAS = 'FT'
    SUBPLACAS = 'DV'
    CAMERAS = 'CM'
    FLEX = 'FL'
    AUTOFALANTES = 'AT'
    LENTES = 'LT'
    TAMPAS = 'TP'
    OUTROS = 'OT'
    CATEGORIAS_PECA = [
        (TELAS, 'Telas'),
        (CONECTORES, 'Conectores'),
        (BOTOES, 'Botoes'),
        (CARCACAS, 'Carcaças'),
        (BATERIAS, 'Baterias'),
        (PLACAS, 'Placas'),
        (SUBPLACAS, 'Sub-placas'),
        (CAMERAS, 'Cameras'),
        (FLEX, 'Flex'),
        (AUTOFALANTES, 'Auto-falantes'),
        (LENTES, 'Lentes'),
        (TAMPAS, 'Tampas'),  
        (OUTROS, 'Outros')
    ]
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_edicao = models.DateTimeField(auto_now=True)
    nome_peca = models.CharField(max_length=99)
    preco_peca = models.DecimalField(max_digits=9, decimal_places=2)
    categoria_peca = models.CharField(max_length=2, choices=CATEGORIAS_PECA, null=True, blank=True)
    quantidade = models.IntegerField()
    codigo_de_barras = models.IntegerField(null=True, blank=True)
    preco_de_custo = models.DecimalField(max_digits=9, decimal_places=2)
    fornecedor = models.CharField(max_length=99, null=True, blank=True)

    def __str__(self):
        return self.nome_peca

    def lucro(self):
         return f'R$ {self.preco_peca - self.preco_de_custo}'
  

   # Resolve when is how will be utility the field quantity 