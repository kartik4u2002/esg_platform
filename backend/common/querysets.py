from django.db import models


class TenantQuerySet(models.QuerySet):
    """QuerySet that filters by organization (tenant)."""

    def for_tenant(self, org):
        """Filter records belonging to the given organization."""
        return self.filter(organization=org)


class TenantManager(models.Manager):
    """Manager that uses TenantQuerySet for tenant-scoped queries."""

    def get_queryset(self):
        return TenantQuerySet(self.model, using=self._db)

    def for_tenant(self, org):
        """Convenience method to filter by tenant on the manager."""
        return self.get_queryset().for_tenant(org)
