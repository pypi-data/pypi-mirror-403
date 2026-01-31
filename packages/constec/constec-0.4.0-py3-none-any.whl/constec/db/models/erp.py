from django.db import models
from .base import UUIDModel
from .company import Company


class System(UUIDModel):
    """ERP system definition - independent of any company.

    An ERP system can be shared across multiple companies via CompanySystem.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    api_endpoint = models.URLField(max_length=200, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        app_label = 'constec_db'
        db_table = 'erp"."systems'

    def __str__(self):
        return f"{self.name}"


class CompanySystem(UUIDModel):
    """Junction table linking companies to ERP systems.

    Allows many-to-many relationship:
    - A company can use multiple ERP systems
    - An ERP system can be used by multiple companies
    """
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="erp_systems",
    )
    system = models.ForeignKey(
        System,
        on_delete=models.CASCADE,
        related_name="company_assignments",
    )
    is_primary = models.BooleanField(
        default=False,
        help_text="Whether this is the primary ERP system for the company"
    )
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        app_label = 'constec_db'
        db_table = 'erp"."company_systems'
        unique_together = [['company', 'system']]
        indexes = [
            models.Index(fields=['company', 'is_primary']),
            models.Index(fields=['system', 'is_active']),
        ]

    def __str__(self):
        primary = " (Primary)" if self.is_primary else ""
        return f"{self.company.name} → {self.system.name}{primary}"


class Connection(UUIDModel):
    """Database connection credentials for an ERP system."""

    DB_TYPE_CHOICES = [
        ('mssql', 'SQL Server'),
        ('postgresql', 'PostgreSQL'),
        ('mysql', 'MySQL'),
    ]

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="erp_connections",
    )
    system = models.ForeignKey(
        System,
        on_delete=models.CASCADE,
        related_name="connections",
    )
    name = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text="Descriptive name for this connection"
    )
    slug = models.CharField(max_length=50)
    db_type = models.CharField(max_length=20, choices=DB_TYPE_CHOICES, default='mssql')
    host = models.CharField(max_length=255)
    port = models.IntegerField()
    database = models.CharField(max_length=100)
    username = models.CharField(max_length=100)
    encrypted_password = models.TextField()
    last_tested_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = 'constec_db'
        db_table = 'erp"."connections'
        unique_together = [['system', 'slug']]

    def __str__(self):
        return f"{self.name}" if self.name else f"{self.system.name} ({self.slug})"
