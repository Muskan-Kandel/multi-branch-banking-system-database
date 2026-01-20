from django.contrib import admin

# Register your models here.

from django.contrib import admin
from .models import Beneficiary, Branch, Customer, Account, Transaction, Loan
admin.site.register(Branch)
admin.site.register(Customer)
admin.site.register(Account)
admin.site.register(Transaction)
admin.site.register(Loan)
admin.site.register(Beneficiary)