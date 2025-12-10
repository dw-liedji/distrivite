from datetime import datetime

from django.db import transaction
from rest_framework import serializers

from apps import organization
from apps.orders import models as order_models
from apps.organization import models as org_models
from apps.users.models import User


class OrganizationUserSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    created = serializers.DateTimeField()
    modified = serializers.DateTimeField()
    org_id = serializers.SerializerMethodField(method_name="get_org_id")
    user_id = serializers.SerializerMethodField(method_name="get_user_id")
    org_slug = serializers.SerializerMethodField(method_name="get_org_slug")

    def get_org_id(self, organization_user: org_models.OrganizationUser):
        return organization_user.organization.id

    def get_org_slug(self, organization_user: org_models.OrganizationUser):
        return organization_user.organization.slug

    def get_user_id(self, organization_user: org_models.OrganizationUser):
        return organization_user.user.id


class StockSerializer(serializers.ModelSerializer):
    organization_slug = serializers.CharField(
        source="organization.slug", read_only=True
    )

    organization_user_name = serializers.CharField(
        source="organization_user.user.username", read_only=True
    )
    id = serializers.UUIDField()
    item_id = serializers.CharField(source="batch.item.id", read_only=True)
    item_name = serializers.CharField(source="batch.item.name", read_only=True)
    category_id = serializers.CharField(source="batch.item.category.id", read_only=True)
    category_name = serializers.CharField(
        source="batch.item.category.name", read_only=True
    )

    batch_number = serializers.CharField(source="batch.batch_number", read_only=True)
    received_date = serializers.CharField(source="batch.received_date", read_only=True)
    expiration_date = serializers.CharField(
        source="batch.expiration_date", read_only=True
    )
    purchase_price = serializers.CharField(
        source="batch.purchase_price", read_only=True
    )
    facturation_price = serializers.CharField(
        source="batch.facturation_price", read_only=True
    )

    is_active = serializers.CharField(source="batch.is_active", read_only=True)

    class Meta:
        model = order_models.Stock
        fields = [
            "id",
            "created",
            "modified",
            "organization_id",
            "organization_slug",
            "organization_user_id",
            "organization_user_name",
            "batch_id",
            "batch_number",
            "item_id",
            "item_name",
            "category_id",
            "category_name",
            "received_date",
            "expiration_date",
            "purchase_price",
            "facturation_price",
            "quantity",
            "is_active",
        ]


class CustomerSerializer(serializers.ModelSerializer):
    organization_slug = serializers.CharField(
        source="organization.slug", read_only=True
    )
    organization_id = serializers.UUIDField()
    id = serializers.UUIDField()

    class Meta:
        model = order_models.Customer
        fields = [
            "id",
            "created",
            "modified",
            "organization_id",
            "organization_slug",
            "name",
            "phone_number",
        ]
        read_only_fields = [
            "organization_slug",
        ]


class TransactionSerializer(serializers.ModelSerializer):
    organization_id = serializers.UUIDField()
    organization_user_id = serializers.UUIDField()
    organization_slug = serializers.CharField(
        source="organization.slug", read_only=True
    )
    organization_user_name = serializers.CharField(
        source="organization_user.user.username", read_only=True
    )
    id = serializers.UUIDField()
    # organization_user_name = serializers.CharField(
    #     source="organization_user.user", read_only=True
    # )

    class Meta:
        model = order_models.Transaction
        fields = [
            "id",
            "created",
            "modified",
            "organization_id",
            "organization_slug",
            "organization_user_id",
            "organization_user_name",
            "participant",
            "transaction_broker",
            "transaction_type",
            "reason",
            "amount",
        ]

        read_only_fields = [
            "organization_slug",
            "organization_user_name",
        ]


class FacturationPaymentSerializer(serializers.ModelSerializer):
    organization_slug = serializers.CharField(
        source="organization.slug", read_only=True
    )

    id = serializers.UUIDField()
    organization_id = serializers.UUIDField()
    organization_user_id = serializers.UUIDField()
    facturation_id = serializers.UUIDField()

    class Meta:
        model = order_models.FacturationPayment
        fields = [
            "id",
            "created",
            "modified",
            "organization_id",
            "organization_slug",
            "organization_user_id",
            "facturation_id",
            "transaction_broker",
            "amount",
        ]


class FacturationStockSerializer(serializers.ModelSerializer):

    id = serializers.UUIDField()
    organization_id = serializers.UUIDField()
    organization_user_id = serializers.UUIDField()
    facturation_id = serializers.UUIDField()
    stock_id = serializers.UUIDField()

    stock_name = serializers.CharField(source="stock.batch.item.name", read_only=True)
    organization_slug = serializers.CharField(
        source="organization.slug", read_only=True
    )

    class Meta:
        model = order_models.FacturationStock
        fields = [
            "id",
            "created",
            "modified",
            "organization_slug",
            "organization_id",
            "organization_user_id",
            "facturation_id",
            "is_delivered",
            "stock_id",
            "stock_name",
            "quantity",
            "unit_price",
        ]


class FacturationSerializer(serializers.ModelSerializer):
    facturation_stocks = FacturationStockSerializer(many=True, required=False)
    facturation_payments = FacturationPaymentSerializer(many=True, required=False)

    id = serializers.UUIDField()
    organization_id = serializers.UUIDField()
    organization_user_id = serializers.UUIDField()
    customer_id = serializers.UUIDField()

    organization_slug = serializers.CharField(
        source="organization.slug", read_only=True
    )
    organization_user_name = serializers.CharField(
        source="organization_user.user.username", read_only=True
    )
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    customer_phone_number = serializers.CharField(
        source="customer.phone_number", read_only=True
    )

    class Meta:
        model = order_models.Facturation
        fields = [
            "id",
            "created",
            "modified",
            "organization_slug",
            "organization_id",
            "organization_user_id",
            "organization_user_name",
            "bill_number",
            "customer_id",
            "customer_name",
            "customer_phone_number",
            "placed_at",
            "is_delivered",
            "facturation_stocks",
            "facturation_payments",
        ]
        # read_only_fields = ["created", "modified"]

    def create(self, validated_data):
        stock_data = validated_data.pop("facturation_stocks", [])
        payment_data = validated_data.pop("facturation_payments", [])

        with transaction.atomic():
            billing = order_models.Facturation.objects.create(**validated_data)

            for item_data in stock_data:
                facturation_stock = order_models.FacturationStock.objects.create(
                    facturation=billing, **item_data
                )

                if facturation_stock.is_delivered:
                    stock = facturation_stock.stock
                    stock.quantity -= facturation_stock.quantity
                    stock.save()

            for pay_data in payment_data:
                order_models.FacturationPayment.objects.create(
                    facturation=billing, **pay_data
                )

        return billing

    def update(self, instance, validated_data):
        stock_data = validated_data.pop("facturation_stocks", [])
        payment_data = validated_data.pop("facturation_payments", [])

        # Update main Facturation fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Simple approach: remove and recreate related data
        with transaction.atomic():
            if stock_data:
                instance.facturation_stocks.all().delete()
                order_models.FacturationStock.objects.bulk_create(
                    [
                        order_models.FacturationStock(facturation=instance, **item)
                        for item in stock_data
                    ]
                )

            if payment_data:
                instance.facturation_payments.all().delete()
                order_models.FacturationPayment.objects.bulk_create(
                    [
                        order_models.FacturationPayment(facturation=instance, **pay)
                        for pay in payment_data
                    ]
                )

        return instance


class FacturationDeliverSerializer(FacturationSerializer):
    def update(self, instance, validated_data):

        with transaction.atomic():
            instance = super().update(instance, validated_data)

            for facturation_stock in instance.facturation_stocks.all():
                stock = facturation_stock.stock
                stock.quantity = stock.quantity - facturation_stock.quantity
                stock.save()

        return instance


class PrepaidAccountSerializer(serializers.ModelSerializer):

    org_slug = serializers.CharField(source="organization.slug", read_only=True)

    class Meta:
        model = order_models.PrepaidAccount
        fields = [
            "customer_id",
            "org_slug",
            "amount",
        ]


class FacturationIdSerializer(serializers.ModelSerializer):

    id = serializers.UUIDField()

    class Meta:
        model = order_models.Facturation
        fields = [
            "id",
        ]


class TransactionIdSerializer(serializers.ModelSerializer):

    id = serializers.UUIDField()

    class Meta:
        model = order_models.Transaction
        fields = [
            "id",
        ]


class CustomerIdSerializer(serializers.ModelSerializer):

    id = serializers.UUIDField()

    class Meta:
        model = order_models.Customer
        fields = [
            "id",
        ]


class StockIdSerializer(serializers.ModelSerializer):

    id = serializers.UUIDField()

    class Meta:
        model = order_models.Stock
        fields = [
            "id",
        ]
