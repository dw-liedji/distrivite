from polymorphic.managers import PolymorphicManager
from apps.core.managers import DataViteManager


class QuantaPolymorphicManager(DataViteManager, PolymorphicManager):
    pass


class CashRegisterManager(DataViteManager):
    pass


class TransactionManager(QuantaPolymorphicManager):
    pass


class ExpenseManager(TransactionManager):
    pass
