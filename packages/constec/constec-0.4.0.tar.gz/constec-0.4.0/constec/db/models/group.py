from django.db import models
from .base import UUIDModel
from .company import Company
from .user import User


class UserGroup(UUIDModel):
    """Hierarchical user groups within a company."""
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="user_groups",
        null=True,
        blank=True
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        related_name="sub_groups",
        null=True,
        blank=True
    )
    users = models.ManyToManyField(
        User,
        related_name="groups"
    )

    class Meta:
        app_label = 'constec_db'
        db_table = 'core"."user_groups'
        unique_together = [['company', 'name']]

    def __str__(self):
        return f"{self.name}"
