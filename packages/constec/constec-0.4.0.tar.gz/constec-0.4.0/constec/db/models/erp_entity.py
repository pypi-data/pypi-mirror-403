from django.core.exceptions import ValidationError
from django.db import models
from .base import UUIDModel
from .company import Company
from .erp import System
from .person import Person


class Role(UUIDModel):
    """Roles within the ERP (customer, supplier, seller)."""
    system = models.ForeignKey(
        System,
        on_delete=models.CASCADE,
        related_name="roles",
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    class Meta:
        app_label = 'constec_db'
        db_table = 'erp"."roles'
        unique_together = [['system', 'name']]

    def __str__(self):
        return f"{self.name}"


class Entity(UUIDModel):
    """Link between ERP external entities and Core persons.

    An Entity can exist without a Person (when someone has ERP access
    but no Core account yet). When they authenticate via CUIT, we can
    optionally link them to a Person later.
    """
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="erp_entities",
    )
    person = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name="erp_entities",
        null=True,
        blank=True,
        help_text="Optional link to Core person"
    )
    system = models.ForeignKey(
        System,
        on_delete=models.CASCADE,
        related_name="entities",
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.PROTECT,
        related_name="entities",
    )
    external_id = models.CharField(
        max_length=255,
        help_text="Entity ID in external ERP system (e.g., cli_Cod, pro_Cod)"
    )
    cuit = models.CharField(
        max_length=13,
        blank=True,
        default='',
        help_text="CUIT without dashes (for authentication lookup)"
    )
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        app_label = 'constec_db'
        db_table = 'erp"."entities'
        verbose_name_plural = 'Entities'
        unique_together = [['company', 'role', 'external_id']]
        indexes = [
            models.Index(fields=['cuit']),
            models.Index(fields=['company', 'cuit']),
        ]

    def clean(self):
        from .erp import CompanySystem
        if not CompanySystem.objects.filter(company=self.company, system=self.system).exists():
            raise ValidationError(
                f"Company {self.company} is not associated with System {self.system}"
            )

    def __str__(self):
        person_info = f"({self.person.full_name})" if self.person else "(no person linked)"
        return f"[{self.system.name}] {self.role.name} {self.external_id} {person_info}"


class EntityAuth(UUIDModel):
    """Authentication credentials for ERP entities.

    Stores hashed passwords for entities that can authenticate via Constancia AI.
    Linked to Entity (which may or may not have a Person linked).
    """
    entity = models.OneToOneField(
        Entity,
        on_delete=models.CASCADE,
        related_name="auth",
        help_text="The ERP entity these credentials belong to"
    )
    password_hash = models.CharField(
        max_length=255,
        help_text="Bcrypt hashed password"
    )
    last_login = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last successful login timestamp"
    )

    class Meta:
        app_label = 'constec_db'
        db_table = 'erp"."entity_auth'
        verbose_name = "Entity Authentication"
        verbose_name_plural = "Entity Authentications"

    def __str__(self):
        status = "active" if self.is_active else "inactive"
        return f"Auth for {self.entity} ({status})"
