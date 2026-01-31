from django.db import models
from .base import UUIDModel


class Organization(UUIDModel):
    """Platform-level tenant (e.g., Constec itself)."""
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        app_label = 'constec_db'
        db_table = 'core"."organizations'

    def __str__(self):
        return self.name


class OrganizationRole(UUIDModel):
    """Roles within an organization."""
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="organization_roles",
        null=True,
        blank=True
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    permissions = models.JSONField(default=dict)
    is_system_role = models.BooleanField(default=False)

    class Meta:
        app_label = 'constec_db'
        db_table = 'core"."organization_roles'
        unique_together = [['organization', 'name']]

    def __str__(self):
        return self.name


class OrganizationUser(UUIDModel):
    """Administrator users at organization level."""
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="users",
    )
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    password_hash = models.CharField(max_length=255)
    role = models.ForeignKey(
        OrganizationRole,
        on_delete=models.PROTECT
    )

    class Meta:
        app_label = 'constec_db'
        db_table = 'core"."organization_users'

    def __str__(self):
        return f"{self.name} ({self.email})"
