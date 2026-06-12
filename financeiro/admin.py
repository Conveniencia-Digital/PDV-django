from django.contrib import admin
from financeiro.models import CardMachine, CardMachineFee, ContasAReceber

admin.site.register(ContasAReceber)
admin.site.register(CardMachine)
admin.site.register(CardMachineFee)
