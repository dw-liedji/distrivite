from django import forms

from apps.cashflow import models
from django.forms import widgets
from django_flatpickr.widgets import (
    DatePickerInput,
    TimePickerInput,
    DateTimePickerInput,
)


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
        model = models.Category
        fields = [
            "organization",
            "name",
            # "description",
        ]
        widgets = {
            "organization": forms.TextInput(
                attrs={
                    "class": "is-hidden",
                }
            ),
        }


class WithdrawalForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        organization = kwargs.pop(
            "organization", None
        )  # Must be pop before the super method

        organization_user = kwargs.pop(
            "organization_user", None
        )  # Must be pop before the super method

        super(WithdrawalForm, self).__init__(*args, **kwargs)
        self.fields["organization"].initial = organization
        self.fields["organization"].label = ""
        self.fields["organization_user"].initial = organization_user
        self.fields["organization_user"].label = ""
        # self.fields["expense"].queryset = models.Expense.objects.filter(
        #     organization=organization
        # )
        self.fields["cash_register"].queryset = models.CashRegister.objects.filter(
            organization=organization
        )

    class Meta:
        model = models.Withdrawal
        fields = [
            "organization",
            "organization_user",
            "cash_register",
            "amount",
            "recipient",
            "reason",
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
        }


class CashRegisterForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        organization = kwargs.pop(
            "organization", None
        )  # Must be pop before the super method
        organization_user = kwargs.pop(
            "organization_user", None
        )  # Must be pop before the super method

        super(CashRegisterForm, self).__init__(*args, **kwargs)
        self.fields["organization"].initial = organization
        self.fields["organization"].label = ""

    class Meta:
        model = models.CashRegister
        fields = [
            "organization",
            "name",
        ]
        widgets = {
            "organization": forms.TextInput(
                attrs={
                    "class": "is-hidden",
                }
            ),
        }


class DepositForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        organization = kwargs.pop(
            "organization", None
        )  # Must be pop before the super method
        print(organization, "this is a child")
        organization_user = kwargs.pop(
            "organization_user", None
        )  # Must be pop before the super method
        print(organization_user, "this is a child")

        super(DepositForm, self).__init__(*args, **kwargs)
        self.fields["organization"].initial = organization
        self.fields["organization"].label = ""
        self.fields["organization_user"].initial = organization_user
        self.fields["organization_user"].label = ""
        self.fields["cash_register"].queryset = models.CashRegister.objects.filter(
            organization=organization
        )

    class Meta:
        model = models.Deposit
        fields = [
            "organization",
            "organization_user",
            "cash_register",
            "operation_date",
            "accounting_date",
            "amount",
            "reason",
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
            "operation_date": DatePickerInput(),
            "accounting_date": DatePickerInput(),
        }


class WithdrawalForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        organization = kwargs.pop(
            "organization", None
        )  # Must be pop before the super method

        organization_user = kwargs.pop(
            "organization_user", None
        )  # Must be pop before the super method

        cash_register = kwargs.pop(
            "cash_register", None
        )  # Must be pop before the super method

        super(WithdrawalForm, self).__init__(*args, **kwargs)
        self.fields["organization"].initial = organization
        self.fields["organization"].label = ""
        self.fields["organization_user"].initial = organization_user
        self.fields["organization_user"].label = ""
        self.fields["cash_register"].queryset = models.CashRegister.objects.filter(
            organization=organization
        )
        self.fields["category"].queryset = models.Category.objects.filter(
            organization=organization
        )

    class Meta:
        model = models.Withdrawal
        fields = [
            "organization",
            "organization_user",
            "category",
            "cash_register",
            "operation_date",
            "accounting_date",
            "amount",
            "recipient",
            "reason",
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
            "operation_date": DatePickerInput(),
            "accounting_date": DatePickerInput(),
        }
