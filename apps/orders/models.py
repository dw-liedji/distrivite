from datetime import datetime
from decimal import Decimal

from django.conf import settings
from django.core.validators import (
    MinValueValidator,
)
from django.db import models

from apps.core.fields import ProfessionalBillNumberField, QuantaField
from apps.core.models import BaseModel
from apps.orders import managers
from apps.organization.models import Organization, OrganizationUser, OrgFeatureManager

User = settings.AUTH_USER_MODEL


class Customer(BaseModel):
    """
    The ``Customer`` model represents a Customer of the online
    store or offline. It wraps Django's built-in ``auth.User`` model, which
    contains information like first and last name, and email, and adds
    phone number and address information.
    """

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    phone_number = models.CharField(
        verbose_name="Téléphone", max_length=20, null=True, blank=True
    )
    credit_limit = models.DecimalField(
        max_digits=19,
        decimal_places=4,
        default=0.0,
        validators=[MinValueValidator(Decimal("0.0"))],
    )
    prepaid_amount = models.DecimalField(
        max_digits=19,
        decimal_places=4,
        default=0.0,
        validators=[MinValueValidator(Decimal("0.0"))],
    )

    objects = OrgFeatureManager()

    class Meta:
        unique_together = [
            # ("organization", "user"),
            # ("organization", "phone_number"),
            # ("organization", "phone_number"),
        ]
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Supplier(BaseModel):
    organization = models.ForeignKey(
        Organization, related_name="suppliers", on_delete=models.CASCADE
    )
    quanta = QuantaField()
    # slug = models.SlugField(max_length=255, unique=True)
    name = models.CharField(
        max_length=255,
    )

    is_active = models.BooleanField(
        default=True,
    )

    objects = managers.BatchManager()

    # def save(self, *args, **kwargs):
    #     self.slug = f"{slugify(self.name)}-{slugify(self.organization.name)}"
    #     super(Product, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.name}"


class Category(BaseModel):
    organization = models.ForeignKey(
        Organization, related_name="categories", on_delete=models.CASCADE
    )
    quanta = QuantaField()
    # slug = models.SlugField(max_length=255, unique=True)
    name = models.CharField(
        max_length=255,
    )

    is_active = models.BooleanField(
        default=True,
    )

    objects = managers.BatchManager()

    class Meta:
        unique_together = [("organization", "name")]

    # def save(self, *args, **kwargs):
    #     self.slug = f"{slugify(self.name)}-{slugify(self.organization.name)}"
    #     super(Product, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.name}"


class Item(BaseModel):
    """
    The ``Product`` model represents a product in the online
    store or offline. It wraps Django's built-in ``auth.User`` model, which
    contains information like first and last name, and email, and adds
    phone number and address information."""

    organization = models.ForeignKey(
        Organization, related_name="items", on_delete=models.CASCADE
    )
    quanta = QuantaField()
    # slug = models.SlugField(max_length=255, unique=True)
    name = models.CharField(max_length=255)

    category = models.ForeignKey(
        Category, related_name="items", on_delete=models.PROTECT
    )

    alert_quantity = models.IntegerField(default=1)
    is_active = models.BooleanField(
        default=True,
    )

    @property
    def is_alert(self):
        return self.alert_quantity > self.total_quantity

    @property
    def total_quantity(self):
        return self.quantity

    @property
    def quantity(self):
        return sum(batch.quantity for batch in self.batchs.all())

    objects = managers.BatchManager()

    # def save(self, *args, **kwargs):
    #     self.slug = f"{slugify(self.name)}-{slugify(self.organization.name)}"
    #     super(Product, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.category})"

    class Meta:
        unique_together = [("organization", "name")]


class Batch(BaseModel):
    """
    The ``Product`` model represents a product in the online
    store or offline. It wraps Django's built-in ``auth.User`` model, which
    contains information like first and last name, and email, and adds
    phone number and address information."""

    organization = models.ForeignKey(
        Organization, related_name="batches", on_delete=models.CASCADE
    )
    quanta = QuantaField()
    # slug = models.SlugField(max_length=255, unique=True)
    item = models.ForeignKey(Item, related_name="batchs", on_delete=models.PROTECT)
    batch_number = models.CharField(max_length=15)
    # category = models.ForeignKey(Category, related_name="batchs", on_delete=models.PROTECT)
    supplier = models.ForeignKey(
        Supplier, related_name="batchs", on_delete=models.PROTECT
    )
    received_date = models.DateField()  # Defaults to today's date
    expiration_date = models.DateField()
    purchase_price = models.DecimalField(
        max_digits=19,
        decimal_places=4,
        validators=[MinValueValidator(Decimal("0.0001"))],
    )
    facturation_price = models.DecimalField(
        max_digits=19,
        decimal_places=4,
        validators=[MinValueValidator(Decimal("0.0001"))],
    )

    # quantity = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField()

    # alert_quantity = models.IntegerField(default=1)
    last_checked = models.DateTimeField(
        null=True, blank=True, help_text="This field is Optional"
    )
    last_maintainer = models.ForeignKey(OrganizationUser, on_delete=models.PROTECT)

    @property
    def is_expired(self):
        return self.expiration_date < datetime.now().date()

    @property
    def is_alert(self):
        return self.quantity <= self.item.alert_quantity

    is_active = models.BooleanField(
        default=True,
    )

    objects = managers.BatchManager()

    # def save(self, *args, **kwargs):
    #     self.slug = f"{slugify(self.name)}-{slugify(self.organization.name)}"
    #     super(Product, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.item.name} ({self.expiration_date}) | {self.facturation_price.quantize(Decimal('1.'))} FCFA"


class Stock(BaseModel):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="stocks"
    )
    organization_user = models.ForeignKey(
        OrganizationUser, on_delete=models.PROTECT, related_name="stocks"
    )
    batch = models.ForeignKey(Batch, on_delete=models.PROTECT, related_name="stocks")
    quantity = models.IntegerField()
    is_active = models.BooleanField(default=True)

    objects = managers.BatchManager()

    def __str__(self):
        return f"{str(self.batch)} - {str(self.organization_user)}"

    class Meta:
        unique_together = ("organization", "organization_user", "batch")
        permissions = [
            ("change_stockprice", "Can change stock price"),
        ]


class AbstractFacturation(BaseModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    # organization_user = models.ForeignKey(
    #     OrganizationUser, on_delete=models.PROTECT, related_name="service_facturations"
    # )
    # facturation = models.ForeignKey(Facturation, on_delete=models.PROTECT)
    bill_number = ProfessionalBillNumberField(unique=False)
    placed_at = models.DateTimeField(auto_now_add=True)
    objects = OrgFeatureManager()

    # def save(self, *args, **kwargs):
    #     if not self.bill_number:
    #         self.bill_number = generate_bill_number()
    #     super(AbstractFacturation, self).save(*args, **kwargs)

    class Meta:
        abstract = True

    @property
    def total_price(self):
        return Decimal(
            sum(
                [
                    item.total_price
                    for item in self.facturation_stocks.all()
                    if item.total_price
                ]
            )
            or 0.0
        )

    @property
    def quantity(self):
        return Decimal(
            sum(
                [
                    item.quantity
                    for item in self.facturation_stocks.all()
                    if item.quantity
                ]
            )
            or 0.0
        )


class AbstractFacturationStock(BaseModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    unit_price = models.DecimalField(max_digits=19, decimal_places=4)
    quantity = models.PositiveIntegerField()
    objects = OrgFeatureManager()

    @property
    def total_price(self):
        return self.quantity * self.unit_price

    @property
    def total_tax(self):
        return self.total_price * self.organization.tax_rate * Decimal(0.01)

    @property
    def total_price_with_tax(self):
        return self.total_price + self.total_tax

    class Meta:
        abstract = True


class Facturation(AbstractFacturation):
    """
    The ``Facturation`` model represents a Customer order. It includes a
    ManyToManyField of products the Customer is ordering and stores
    the date and total price information.
    """

    customer = models.ForeignKey(
        Customer, on_delete=models.PROTECT, related_name="facturations"
    )
    custom_customer = models.CharField(max_length=100, null=True, blank=True)
    organization_user = models.ForeignKey(OrganizationUser, on_delete=models.PROTECT)

    is_delivered = models.BooleanField(default=True)
    is_proforma = models.BooleanField(default=False)
    objects = managers.FacturationManager()

    class Meta:
        permissions = [
            ("deliver_facturation", "Can deliver facturation"),
            ("print_facturation", "Can print facturation"),
        ]

    def __str__(self) -> str:
        return f"{self.customer} | {self.bill_number}"

    @property
    def total_amount_paid(self):
        """Calculate total amount already paid for this facturation"""
        return sum([payment.amount for payment in self.facturation_payments.all()])

    @property
    def total_remaining_balance(self):
        """Calculate remaining balance to be paid"""
        return self.total_price - self.total_amount_paid


class FacturationStock(AbstractFacturationStock):
    """
    The ``FacturationStock`` model represents information about a
    specific product ordered by a patient.
    """

    stock = models.ForeignKey(
        Stock, on_delete=models.PROTECT, related_name="facturation_stocks"
    )
    organization_user = models.ForeignKey(OrganizationUser, on_delete=models.PROTECT)
    facturation = models.ForeignKey(
        Facturation, on_delete=models.CASCADE, related_name="facturation_stocks"
    )
    is_delivered = models.BooleanField(default=False)
    unit_price = models.DecimalField(
        max_digits=19,
        decimal_places=6,
    )

    class Meta:
        unique_together = ("organization", "facturation", "stock")
        permissions = [
            ("deliver_facturationstock", "Can deliver facturation stock"),
        ]

    def __str__(self) -> str:
        return f"{self.quantity} {self.stock.batch.item.name}"


class TransactionBroker(models.TextChoices):
    CASHIER = ("cashier", "Cashier")
    ORANGE_MONEY = ("orange_money", "Orange Money")
    MTN_MOBILE_MONEY = ("mtn_mobile_money", "MTN Mobile Money")


class TransactionType(models.TextChoices):
    WITHDRAWAL = ("withdrawal", "Withdrawal")
    DEPOSIT = ("deposit", "Deposit")


class Transaction(BaseModel):
    organization = models.ForeignKey(
        Organization, related_name="transactions", on_delete=models.CASCADE
    )
    organization_user = models.ForeignKey(
        OrganizationUser, on_delete=models.PROTECT, related_name="transactions"
    )
    transaction_broker = models.CharField(
        max_length=20,
        choices=TransactionBroker.choices,
        default=TransactionBroker.CASHIER,
    )
    transaction_type = models.CharField(
        choices=TransactionType.choices,
        max_length=20,
    )
    amount = models.DecimalField(max_digits=19, decimal_places=3)
    participant = models.CharField(max_length=100)
    reason = models.CharField(max_length=100)
    objects = managers.DataViteManager()

    class Meta:
        permissions = [
            ("print_transaction", "Can print transaction"),
        ]


class BulkCreditPayment(BaseModel):
    bill_number = ProfessionalBillNumberField(unique=False)

    customer = models.ForeignKey(
        Customer, related_name="bulk_credit_payments", on_delete=models.CASCADE
    )
    organization = models.ForeignKey(
        Organization, related_name="bulk_credit_payments", on_delete=models.CASCADE
    )
    organization_user = models.ForeignKey(
        OrganizationUser, on_delete=models.PROTECT, related_name="bulk_credit_payments"
    )
    transaction_broker = models.CharField(
        max_length=20,
        choices=TransactionBroker.choices,
        default=TransactionBroker.CASHIER,
    )
    amount = models.DecimalField(max_digits=19, decimal_places=3)
    objects = OrgFeatureManager()


class FacturationPayment(BaseModel):
    facturation = models.ForeignKey(
        Facturation, related_name="facturation_payments", on_delete=models.CASCADE
    )
    organization = models.ForeignKey(
        Organization, related_name="facturation_payments", on_delete=models.CASCADE
    )
    bulk_credit_payment = models.ForeignKey(
        BulkCreditPayment,
        on_delete=models.CASCADE,
        related_name="facturation_payments",
        null=True,
        blank=True,
    )
    organization_user = models.ForeignKey(
        OrganizationUser, on_delete=models.PROTECT, related_name="facturation_payments"
    )
    transaction_broker = models.CharField(
        max_length=20,
        choices=TransactionBroker.choices,
        default=TransactionBroker.CASHIER,
    )
    amount = models.DecimalField(max_digits=19, decimal_places=3)
    objects = OrgFeatureManager()


class FacturationRefund(BaseModel):
    organization = models.ForeignKey(
        Organization,
        related_name="facturation_FacturationRefunds",
        on_delete=models.CASCADE,
    )
    facturation = models.ForeignKey(
        Facturation,
        on_delete=models.PROTECT,
        related_name="facturation_FacturationRefunds",
    )
    bill_number = ProfessionalBillNumberField(unique=False)
    organization_user = models.ForeignKey(
        OrganizationUser,
        on_delete=models.PROTECT,
        related_name="facturation_FacturationRefunds",
    )
    amount = models.DecimalField(max_digits=19, decimal_places=3)
    objects = OrgFeatureManager()

    class Meta:
        unique_together = [
            (
                "organization",
                "bill_number",
            )
        ]
