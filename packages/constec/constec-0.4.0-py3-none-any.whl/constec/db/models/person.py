from django.db import models
from .base import UUIDModel
from .company import Company


class Person(UUIDModel):
    """Real person (customer, supplier, employee)."""
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="persons",
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    full_name = models.CharField(max_length=255)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        app_label = 'constec_db'
        db_table = 'core"."persons'

    def __str__(self):
        return f"{self.full_name}"

    def save(self, *args, **kwargs):
        """Auto-generate full_name from first_name and last_name."""
        self.full_name = f"{self.first_name} {self.last_name}"
        super().save(*args, **kwargs)
