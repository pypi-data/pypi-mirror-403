from django.db import models
from .base import UUIDModel
from .company import Company
from .organization import Organization


class Module(UUIDModel):
    """Available modules in the platform."""
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, null=True)
    description = models.TextField(blank=True, null=True)
    version = models.CharField(max_length=20)

    class Meta:
        app_label = 'constec_db'
        db_table = 'core"."modules'

    def __str__(self):
        return f"{self.name}"


class CompanyModule(UUIDModel):
    """Modules enabled per company."""
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="company_modules",
    )
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name="company_modules",
    )
    is_enabled = models.BooleanField(default=True)
    settings = models.JSONField(default=dict, blank=True)

    class Meta:
        app_label = 'constec_db'
        db_table = 'core"."company_modules'
        unique_together = [['company', 'module']]

    def __str__(self):
        return f"{self.company.name} - {self.module.name}"


class OrganizationModule(UUIDModel):
    """Modules enabled per organization."""
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="organization_modules",
    )
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name="organization_modules",
    )
    is_enabled = models.BooleanField(default=True)
    settings = models.JSONField(default=dict, blank=True)

    class Meta:
        app_label = 'constec_db'
        db_table = 'core"."organization_modules'
        unique_together = [['organization', 'module']]

    def __str__(self):
        return f"{self.organization.name} - {self.module.name}"
