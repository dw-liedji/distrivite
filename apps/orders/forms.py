from dal import autocomplete
from django import forms
from django_flatpickr import schemas as flatpickr_schemas
from django_flatpickr import widgets as flatpickr_widgets
from phonenumber_field.formfields import PhoneNumberField

from apps.orders import models as order_models
from apps.orders.widgets import HTMXAutoCompleteWidget
from apps.organization import models as org_models


class CustomerForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        organization = kwargs.pop(
            "organization", None
        )  # Must be pop before the super method
        organization_user = kwargs.pop(
            "organization_user", None
        )  # Must be pop before the super method

        super(CustomerForm, self).__init__(*args, **kwargs)
        self.fields["organization"].initial = organization
        self.fields["organization"].label = ""

    class Meta:
        model = order_models.Customer
        fields = ["organization", "name", "phone_number", "credit_limit"]
        widgets = {
            "organization": forms.TextInput(
                attrs={
                    "class": "is-hidden",
                }
            ),
        }


class StockForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        organization = kwargs.pop(
            "organization", None
        )  # Must be pop before the super method
        organization_user = kwargs.pop(
            "organization_user", None
        )  # Must be pop before the super method

        super(StockForm, self).__init__(*args, **kwargs)
        self.fields["organization"].initial = organization
        self.fields["organization"].label = ""
        self.fields["organization_user"].queryset = (
            order_models.OrganizationUser.objects.filter(organization=organization)
        )

    class Meta:
        model = order_models.Stock
        fields = ["organization", "organization_user", "batch", "quantity", "is_active"]
        widgets = {
            "organization": forms.TextInput(
                attrs={
                    "class": "is-hidden",
                }
            ),
            "batch": autocomplete.ModelSelect2(
                url="core:batch-autocomplete",
                forward=["organization"],
            ),
        }


class BatchForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        organization = kwargs.pop(
            "organization", None
        )  # Must be pop before the super method
        organization_user = kwargs.pop(
            "organization_user", None
        )  # Must be pop before the super method

        super(BatchForm, self).__init__(*args, **kwargs)
        self.fields["organization"].initial = organization
        self.fields["organization"].label = ""
        self.fields["last_maintainer"].initial = organization_user
        self.fields["last_maintainer"].label = ""
        self.fields["item"].queryset = order_models.Item.objects.filter(
            organization=organization
        ).order_by("name")
        self.fields["supplier"].queryset = order_models.Supplier.objects.filter(
            organization=organization
        ).order_by("name")

    class Meta:
        model = order_models.Batch
        fields = [
            "organization",
            # "category",
            # "name",
            "item",
            "batch_number",
            "supplier",
            "received_date",
            "expiration_date",
            # "Category_choice",
            "purchase_price",
            "facturation_price",
            "quantity",
            # "emergency_quantity",
            # "alert_quantity",
            "is_active",
            "last_checked",
            "last_maintainer",
        ]
        widgets = {
            "organization": forms.TextInput(
                attrs={
                    "class": "is-hidden",
                }
            ),
            "last_maintainer": forms.TextInput(
                attrs={
                    "class": "is-hidden",
                }
            ),
            # "name": forms.TextInput(
            #     attrs={
            #         "class": "",
            #     }
            # ),
            "item": autocomplete.ModelSelect2(
                url="core:item-autocomplete",
                forward=["organization"],
            ),
            "last_checked": flatpickr_widgets.DateTimePickerInput(),
            "expiration_date": flatpickr_widgets.DatePickerInput(),
            "received_date": flatpickr_widgets.DatePickerInput(),
        }


class ItemForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        organization = kwargs.pop(
            "organization", None
        )  # Must be pop before the super method
        organization_user = kwargs.pop(
            "organization_user", None
        )  # Must be pop before the super method

        super(ItemForm, self).__init__(*args, **kwargs)
        self.fields["organization"].initial = organization
        self.fields["organization"].label = ""
        # self.fields["last_maintainer"].initial = organization_user
        # self.fields["last_maintainer"].label = ""
        # self.fields["supplier"].queryset = order_models.Supplier.objects.filter(
        #     organization=organization
        # )
        self.fields["category"].queryset = order_models.Category.objects.filter(
            organization=organization
        ).order_by("name")

    class Meta:
        model = order_models.Item
        fields = [
            "organization",
            "category",
            "name",
            # "batch_number",
            # "supplier",
            # "expiration_date",
            # "Category_choice",
            # "purchase_price",
            # "facturation_price",
            # "quantity",
            # "emergency_quantity",
            "alert_quantity",
            "is_active",
            # "last_checked",
            # "last_maintainer",
        ]
        widgets = {
            "organization": forms.TextInput(
                attrs={
                    "class": "is-hidden",
                }
            ),
            # "last_maintainer": forms.TextInput(
            #     attrs={
            #         "class": "is-hidden",
            #     }
            # ),
            "name": forms.TextInput(
                attrs={
                    "class": "",
                }
            ),
            "category": autocomplete.ModelSelect2(
                url="core:category-autocomplete",
                forward=["organization"],
            ),
            # "last_checked": flatpickr_widgets.DateTimePickerInput(),
            # "expiration_date": flatpickr_widgets.DatePickerInput(),
        }


class SupplierForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        organization = kwargs.pop(
            "organization", None
        )  # Must be pop before the super method
        organization_user = kwargs.pop(
            "organization_user", None
        )  # Must be pop before the super method

        super(SupplierForm, self).__init__(*args, **kwargs)
        self.fields["organization"].initial = organization
        self.fields["organization"].label = ""

    class Meta:
        model = order_models.Supplier
        fields = [
            "organization",
            "name",
            "is_active",
        ]
        widgets = {
            "organization": forms.TextInput(
                attrs={
                    "class": "is-hidden",
                }
            ),
            "name": forms.TextInput(
                attrs={
                    "class": "",
                }
            ),
        }


class CategoryForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        organization = kwargs.pop(
            "organization", None
        )  # Must be pop before the super method
        organization_user = kwargs.pop(
            "organization_user", None
        )  # Must be pop before the super method

        super(CategoryForm, self).__init__(*args, **kwargs)
        self.fields["organization"].initial = organization
        self.fields["organization"].label = ""

    class Meta:
        model = order_models.Category
        fields = [
            "organization",
            "name",
            "is_active",
        ]
        widgets = {
            "organization": forms.TextInput(
                attrs={
                    "class": "is-hidden",
                }
            ),
            "name": forms.TextInput(
                attrs={
                    "class": "",
                }
            ),
        }


class FacturationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        organization = kwargs.pop(
            "organization", None
        )  # Must be pop before the super method
        print(organization, "this is a father")

        organization_user = kwargs.pop(
            "organization_user", None
        )  # Must be pop before the super method

        super(FacturationForm, self).__init__(*args, **kwargs)
        self.fields["organization"].initial = organization
        self.fields["organization"].label = ""
        self.fields["organization_user"].initial = organization_user
        self.fields["organization_user"].label = ""
        self.fields["customer"].queryset = (
            order_models.Customer.objects.for_organization(organization=organization)
        )

    class Meta:
        model = order_models.Facturation
        fields = [
            "organization",
            "organization_user",
            "customer",
            "custom_customer",
            "is_delivered",
        ]

        widgets = {
            "organization": forms.TextInput(
                attrs={
                    "class": "is-hidden",
                }
            ),
            "organization_user": forms.TextInput(
                attrs={
                    "class": "is-hidden",
                }
            ),
            # "consultation": CKEditorWidget(),
            "delivered_time": flatpickr_widgets.DateTimePickerInput(),
            # "patient": HTMXAutoCompleteWidget(
            #     view_name="core:patient-autocomplete",
            #     forwarded_fields=["organization"],
            # ),
            # "patient": autocomplete.ModelSelect2(
            #     url="core:patient-autocomplete",
            #     forward=["organization"],
            # ),
            "customer": autocomplete.ModelSelect2(
                url="core:customer-autocomplete",
                forward=["organization"],
            ),
        }


class FacturationStockForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):

        organization = kwargs.pop(
            "organization", None
        )  # Must be pop before the super method

        organization_user = kwargs.pop(
            "organization_user", None
        )  # Must be pop before the super method

        facturation = kwargs.pop(
            "facturation", None
        )  # Must be pop before the super method

        # print(organization, "this is a child")
        super(FacturationStockForm, self).__init__(*args, **kwargs)
        self.fields["organization"].initial = organization
        self.fields["organization"].label = ""
        self.fields["organization_user"].initial = organization_user
        self.fields["organization_user"].label = ""
        self.fields["facturation"].initial = facturation
        self.fields["facturation"].label = ""
        self.fields["stock"].queryset = order_models.Stock.objects.filter(
            organization=organization
        )

    class Meta:
        model = order_models.FacturationStock
        fields = [
            "organization",
            "organization_user",
            "facturation",
            "stock",
            "quantity",
            "unit_price",
        ]

        widgets = {
            "organization": forms.TextInput(
                attrs={
                    "class": "is-hidden",
                }
            ),
            "organization_user": forms.TextInput(
                attrs={
                    "class": "is-hidden",
                }
            ),
            "facturation": forms.TextInput(
                attrs={
                    "class": "is-hidden",
                }
            ),
            "stock": autocomplete.ModelSelect2(
                url="core:stock-autocomplete",
                forward=["organization"],
            ),
        }


class FacturationPaymentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        organization = kwargs.pop(
            "organization", None
        )  # Must be pop before the super method

        organization_user = kwargs.pop(
            "organization_user", None
        )  # Must be pop before the super method

        organization_user = kwargs.pop(
            "organization_user", None
        )  # Must be pop before the super method

        print(organization, "this is a child")
        super(FacturationPaymentForm, self).__init__(*args, **kwargs)
        self.fields["organization"].initial = organization
        self.fields["organization"].label = ""
        self.fields["organization_user"].initial = organization_user
        self.fields["organization_user"].label = ""

    class Meta:
        model = order_models.FacturationPayment
        fields = [
            "organization",
            "facturation",
            "transaction_broker",
            "organization_user",
            "amount",
        ]

        widgets = {
            "organization": forms.TextInput(
                attrs={
                    "class": "is-hidden",
                }
            ),
            "facturation": forms.TextInput(
                attrs={
                    "class": "is-hidden",
                }
            ),
            "organization_user": forms.TextInput(
                attrs={
                    "class": "is-hidden",
                }
            ),
            "customer": autocomplete.ModelSelect2(
                url="core:customer-autocomplete",
                forward=["organization"],
            ),
        }


class FacturationRefundForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        organization = kwargs.pop(
            "organization", None
        )  # Must be pop before the super method
        print(organization, "this is a father")

        organization_user = kwargs.pop(
            "organization_user", None
        )  # Must be pop before the super method

        facturation = kwargs.pop(
            "facturation", None
        )  # Must be pop before the super method

        super(FacturationRefundForm, self).__init__(*args, **kwargs)
        self.fields["organization"].initial = organization
        self.fields["organization"].label = ""
        self.fields["organization_user"].initial = organization_user
        self.fields["organization_user"].label = ""
        self.fields["facturation"].initial = facturation
        self.fields["facturation"].label = ""

    class Meta:
        model = order_models.FacturationRefund
        fields = [
            "organization",
            "organization_user",
            "facturation",
            "amount",
        ]

        widgets = {
            "organization": forms.TextInput(
                attrs={
                    "class": "is-hidden",
                }
            ),
            "facturation": forms.TextInput(
                attrs={
                    "class": "is-hidden",
                }
            ),
            "organization_user": forms.TextInput(
                attrs={
                    "class": "is-hidden",
                }
            ),
            # "consultation": CKEditorWidget(),
            "delivered_time": flatpickr_widgets.DateTimePickerInput(),
            # "patient": HTMXAutoCompleteWidget(
            #     view_name="core:patient-autocomplete",
            #     forwarded_fields=["organization"],
            # ),
            # "patient": autocomplete.ModelSelect2(
            #     url="core:patient-autocomplete",
            #     forward=["organization"],
            # ),
            "customer": autocomplete.ModelSelect2(
                url="core:customer-autocomplete",
                forward=["organization"],
            ),
        }


class TransactionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        organization = kwargs.pop("organization", None)
        organization_user = kwargs.pop("organization_user", None)

        super(TransactionForm, self).__init__(*args, **kwargs)

        self.fields["organization"].initial = organization
        self.fields["organization"].label = ""

        if organization_user:
            self.fields["organization_user"].initial = organization_user
            self.fields["organization_user"].label = ""

    class Meta:
        model = order_models.Transaction
        fields = [
            "organization",
            "organization_user",
            "transaction_broker",
            "transaction_type",
            "amount",
            "participant",
            "reason",
        ]
        widgets = {
            "organization": forms.HiddenInput(),
            "organization_user": forms.HiddenInput(),
            "transaction_broker": forms.Select(
                attrs={
                    "class": "select",
                }
            ),
            "transaction_type": forms.Select(
                attrs={
                    "class": "select",
                }
            ),
            "amount": forms.NumberInput(
                attrs={
                    "class": "input",
                    "placeholder": "0.000",
                    "step": "0.001",
                }
            ),
            "participant": forms.TextInput(
                attrs={
                    "class": "input",
                    "placeholder": "Participant name",
                }
            ),
            "reason": forms.TextInput(
                attrs={
                    "class": "input",
                    "placeholder": "Reason for transaction",
                }
            ),
        }


class BulkCreditPaymentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        organization = kwargs.pop(
            "organization", None
        )  # Must be pop before the super method

        organization_user = kwargs.pop(
            "organization_user", None
        )  # Must be pop before the super method
        print("this is a organization_user from attributes", organization_user)

        print(organization, "this is a child")
        super(BulkCreditPaymentForm, self).__init__(*args, **kwargs)
        self.fields["organization"].initial = organization
        self.fields["organization"].label = ""
        self.fields["organization_user"].initial = organization_user
        self.fields["organization_user"].label = ""

    class Meta:
        model = order_models.BulkCreditPayment
        fields = [
            "organization",
            "customer",
            "transaction_broker",
            "organization_user",
            "amount",
        ]

        widgets = {
            "organization": forms.TextInput(
                attrs={
                    "class": "is-hidden",
                }
            ),
            "facturation": forms.TextInput(
                attrs={
                    "class": "is-hidden",
                }
            ),
            "organization_user": forms.TextInput(
                attrs={
                    "class": "is-hidden",
                }
            ),
            "customer": autocomplete.ModelSelect2(
                url="core:customer-autocomplete",
                forward=["organization"],
            ),
        }
