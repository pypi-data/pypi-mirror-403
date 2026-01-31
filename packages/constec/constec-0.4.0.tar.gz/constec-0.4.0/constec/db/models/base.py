import uuid
from django.db import models


class UUIDModel(models.Model):
    """Base model with UUID primary key and common audit fields.

    All Constec models inherit from this to ensure consistent
    UUID-based primary keys and audit fields across the platform.

    Fields provided:
        - id: UUID primary key
        - is_active: soft delete flag
        - created_at: auto-set on creation
        - updated_at: auto-set on every save
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
