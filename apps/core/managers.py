from django_pandas.managers import DataFrameManager

from apps.organization.managers import (
    OrgFeatureManager,
    OrgUserManager,
    OrgOwnerManager,
)


class DataViteManager(DataFrameManager, OrgFeatureManager):
    pass


class DataViteUserManager(DataFrameManager, OrgFeatureManager, OrgUserManager):
    pass


class DataViteOwnerManager(DataFrameManager, OrgFeatureManager, OrgUserManager):
    pass
