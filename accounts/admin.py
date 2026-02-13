# accounts/admin.py

from django.contrib import admin
from .models import Branch, Customer, Account, Transaction, Loan, Beneficiary


# ============================================
# BRANCH ADMIN
# ============================================
@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'address', 'contact_number')
    search_fields = ('name', 'address')
    list_per_page = 20


# ============================================
# CUSTOMER ADMIN
# ============================================
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_username', 'phone', 'address')
    search_fields = ('user__username', 'phone')
    list_per_page = 20
    
    def get_username(self, obj):
        return obj.user.username
    get_username.short_description = 'Username'


# ============================================
# ACCOUNT ADMIN
# ============================================
@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_customer', 'account_type', 'balance', 'branch', 'is_active', 'created_at')
    list_filter = ('account_type', 'is_active', 'branch')
    search_fields = ('customer__user__username',)
    list_per_page = 20
    readonly_fields = ('created_at', 'updated_at')
    
    def get_customer(self, obj):
        return obj.customer.user.username
    get_customer.short_description = 'Customer'


# ============================================
# TRANSACTION ADMIN
# ============================================
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_account', 'transaction_type', 'amount', 'timestamp', 'description')
    list_filter = ('transaction_type', 'timestamp')
    search_fields = ('account__customer__user__username', 'description')
    date_hierarchy = 'timestamp'
    list_per_page = 50
    readonly_fields = ('timestamp',)
    
    def get_account(self, obj):
        return f"Account #{obj.account.id} - {obj.account.customer.user.username}"
    get_account.short_description = 'Account'


# ============================================
# LOAN ADMIN
# ============================================
@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_customer', 'amount', 'interest_rate', 'status', 'start_date', 'end_date', 'branch')
    list_filter = ('status', 'branch')
    search_fields = ('customer__user__username',)
    list_per_page = 20
    
    def get_customer(self, obj):
        return obj.customer.user.username
    get_customer.short_description = 'Customer'


# ============================================
# BENEFICIARY ADMIN
# ============================================
@admin.register(Beneficiary)
class BeneficiaryAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_customer', 'name', 'account_number', 'bank_name', 'ifsc_code')
    search_fields = ('name', 'account_number', 'bank_name', 'customer__user__username')
    list_per_page = 20
    
    def get_customer(self, obj):
        return obj.customer.user.username
    get_customer.short_description = 'Customer'