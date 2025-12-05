import decimal

from django.contrib.auth import get_user_model
from django.contrib.humanize.templatetags.humanize import intcomma
from django.db import models
from django.db.models import Sum
from polymorphic.models import PolymorphicModel

from apps.cashflow import managers
from apps.core.fields import ProfessionalBillNumberField, QuantaField
from apps.core.models import BaseModel
from apps.organization.models import Organization, OrganizationUser

User = get_user_model()


class CashRegister(BaseModel):
    name = models.CharField(max_length=30)
    organization = models.ForeignKey(
        Organization, related_name="cash_registers", on_delete=models.CASCADE
    )
    objects = managers.CashRegisterManager()

    class Meta:
        unique_together = [("organization", "name")]

    @property
    def balance(self):
        return self.total_deposit - self.total_withdrawal

    @property
    def total_withdrawal(self):
        return Withdrawal.objects.filter(
            cash_register=self, is_validated=True
        ).aggregate(total=Sum("amount"))["total"] or decimal.Decimal(0.0)

    @property
    def total_deposit(self):
        return Deposit.objects.filter(cash_register=self).aggregate(
            total=Sum("amount")
        )["total"] or decimal.Decimal(0.0)

    def __str__(self):
        return self.name


class Transaction(BaseModel, PolymorphicModel):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="expenses"
    )
    cash_register = models.ForeignKey(
        CashRegister, on_delete=models.CASCADE, related_name="transactions"
    )
    accounting_date = models.DateField(
        help_text="Date the traitement par la compabilité"
    )

    operation_date = models.DateField(help_text="Date of the operation (transaction)")

    bill_number = ProfessionalBillNumberField()
    organization_user = models.ForeignKey(
        OrganizationUser,
        on_delete=models.PROTECT,
        related_name="organization_users",
    )
    amount = models.DecimalField(max_digits=19, decimal_places=4)
    reason = models.CharField(max_length=255)
    objects = managers.TransactionManager()


class Category(BaseModel):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="expense_categories",
    )
    name = models.CharField(max_length=100)
    # description = models.CharField(max_length=255)
    objects = managers.DataViteManager()

    class Meta:
        unique_together = [("organization", "name")]

    def __str__(self) -> str:
        return self.name


class Deposit(Transaction):

    @property
    def value(self):
        return abs(self.amount)

    @property
    def display_amount(self):
        return f"[+] {intcomma(int(abs(self.amount)))}"

    @property
    def is_deposit(self):
        return True

    @property
    def display_participant(self):
        return f"{self.organization_user.user }"

    @property
    def display_user(self):
        return f"{str(self.organization_user.user) }"

    def __str__(self):
        return f"[+] Dépot de {self.amount} dans la caisse {self.cash_register.name} pour {self.reason}"


class Withdrawal(Transaction):
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="expenses"
    )
    recipient = models.CharField(max_length=255)
    is_validated = models.BooleanField(default=False)
    objects = managers.ExpenseManager()

    @property
    def display_user(self):
        return f"{ str(self.organization_user.user)}"

    @property
    def display_amount(self):
        return f"[-] {intcomma(int(abs(self.amount)))}"

    @property
    def display_participant(self):
        return f"{self.recipient}"

    @property
    def is_deposit(self):
        return False

    @property
    def value(self):
        return -abs(self.amount)

    def __str__(self):
        return f"[-] Rétrait de {self.amount} de la caisse {self.cash_register.name} pour {self.reason}"

    class Meta:
        permissions = [
            ("cashflow.validate_withdrawal", "Can validate withdrawal"),
        ]
