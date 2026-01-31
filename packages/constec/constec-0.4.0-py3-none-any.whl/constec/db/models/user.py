from django.db import models
from .base import UUIDModel
from .company import Company


class User(UUIDModel):
    """User belonging to a company."""
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="users"
    )
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    password_hash = models.CharField(max_length=255)

    class Meta:
        app_label = 'constec_db'
        db_table = 'core"."users'

    def __str__(self):
        return f"{self.name} ({self.email})"


class UserRole(UUIDModel):
    """Role within a company."""
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="user_roles",
        null=True,
        blank=True
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    permissions = models.JSONField(default=dict)
    is_system_role = models.BooleanField(default=False)

    class Meta:
        app_label = 'constec_db'
        db_table = 'core"."user_roles'
        unique_together = [['company', 'name']]

    def __str__(self):
        return f"{self.name}"


class UserCompanyAccess(UUIDModel):
    """Cross-company access: one User can access multiple Companies."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="company_accesses",
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="user_accesses",
    )
    role = models.ForeignKey(
        UserRole,
        on_delete=models.PROTECT,
        related_name="user_accesses",
    )

    class Meta:
        app_label = 'constec_db'
        db_table = 'core"."user_company_access'
        verbose_name = 'User company access'
        verbose_name_plural = 'User company access'
        unique_together = [['user', 'company']]

    def __str__(self):
        return f"{self.user.email} @ {self.company.name} ({self.role.name})"
