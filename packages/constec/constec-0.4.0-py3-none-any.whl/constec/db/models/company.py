from django.db import models
from django.core.exceptions import ValidationError
from .base import UUIDModel
from .organization import Organization


class Company(UUIDModel):
    """Client company, belongs to an Organization."""
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="companies",
    )
    name = models.CharField(max_length=255)
    legal_name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=100, unique=True)
    parent_company = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='children'
    )
    website = models.URLField(blank=True, null=True)

    class Meta:
        app_label = 'constec_db'
        db_table = 'core"."companies'
        verbose_name_plural = 'Companies'

    def __str__(self):
        return self.name

    def clean(self):
        if self.parent_company == self:
            raise ValidationError('A company cannot be its own parent')
