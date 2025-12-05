from django.contrib import admin

# Register your models here.

from django.contrib import admin

from .models import CashRegister, Withdrawal


@admin.register(CashRegister)
class CashRegisterAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "organization",
    ]
    list_filter = ["name", "organization"]
    search_fields = ["name"]
    # other configurations for the admin interface


from .models import Deposit


@admin.register(Deposit)
class DepositAdmin(admin.ModelAdmin):
    list_display = [
        "organization",
        "cash_register",
        "amount",
    ]
    list_filter = [
        "organization",
    ]
    search_fields = ["cash_register"]
    # other configurations for the admin interface


@admin.register(Withdrawal)
class WithdrawalAdmin(admin.ModelAdmin):
    list_display = [
        "organization",
        "cash_register",
        "amount",
    ]
    list_filter = [
        "organization",
    ]
    search_fields = ["cash_register"]
    # other configurations for the admin interface
