from django.db import models
from .base import UUIDModel
from .person import Person


class ContactType(UUIDModel):
    """Types of contact (email, phone, etc)."""
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)

    class Meta:
        app_label = 'constec_db'
        db_table = 'core"."contact_types'

    def __str__(self):
        return f"{self.name}"


class Contact(UUIDModel):
    """Contact value."""
    type = models.ForeignKey(
        ContactType,
        on_delete=models.CASCADE,
        related_name="contacts",
    )
    label = models.CharField(max_length=100, blank=True, help_text="Optional label (e.g. 'Personal', 'Work')")
    value = models.CharField(max_length=255)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        app_label = 'constec_db'
        db_table = 'core"."contacts'

    def __str__(self):
        if self.label:
            return f"{self.label}: {self.value} ({self.type.name})"
        return f"{self.value} ({self.type.name})"


class PersonContact(UUIDModel):
    """Person-contact relationship."""
    person = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name="person_contacts",
    )
    contact = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE,
        related_name="person_contacts",
    )
    is_primary = models.BooleanField(default=False)

    class Meta:
        app_label = 'constec_db'
        db_table = 'core"."person_contacts'
        unique_together = [['person', 'contact']]

    def __str__(self):
        return f"{self.person.full_name} - {self.contact.value} ({self.contact.type.name})"

    def save(self, *args, **kwargs):
        """Remove is_primary from other contacts of the same type for this person."""
        if self.is_primary:
            PersonContact.objects.filter(
                person=self.person,
                contact__type=self.contact.type,
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)

        super().save(*args, **kwargs)
