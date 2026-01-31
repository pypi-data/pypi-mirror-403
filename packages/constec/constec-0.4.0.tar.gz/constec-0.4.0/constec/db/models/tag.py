from django.db import models
from .base import UUIDModel
from .person import Person
from .company import Company


class TagCategory(UUIDModel):
    """Tag categories per company."""
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="tag_categories",
    )
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)

    class Meta:
        app_label = 'constec_db'
        db_table = 'core"."tag_categories'
        verbose_name = 'Tag category'
        verbose_name_plural = 'Tag categories'

    def __str__(self):
        return f"{self.name}"


class PersonTag(UUIDModel):
    """Tags for persons."""
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="person_tags",
    )
    category = models.ForeignKey(
        TagCategory,
        on_delete=models.CASCADE,
        related_name="person_tags",
    )
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, blank=True, null=True)

    class Meta:
        app_label = 'constec_db'
        db_table = 'core"."person_tags'
        unique_together = [['company', 'category', 'name']]

    def __str__(self):
        return f"{self.name}"


class PersonTagged(UUIDModel):
    """Person-tag relationship."""
    person = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name="tagged_items",
    )
    tag = models.ForeignKey(
        PersonTag,
        on_delete=models.CASCADE,
        related_name="tagged_persons",
    )

    class Meta:
        app_label = 'constec_db'
        db_table = 'core"."person_tagged'
        unique_together = [['person', 'tag']]

    def __str__(self):
        return f"{self.person.full_name} - {self.tag.name}"
