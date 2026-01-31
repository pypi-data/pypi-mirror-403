from django.db import models
from .base import UUIDModel
from .organization import Organization, OrganizationUser
from .company import Company


class FlowTemplate(UUIDModel):
    """Global flow templates available to all companies.

    Created by organization admins. Companies can use these
    templates as-is or customize them.
    """

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="flow_templates",
        null=True,
        blank=True,
        help_text="Organization that owns this template (null for global)"
    )

    name = models.CharField(max_length=100)
    description = models.TextField()
    category = models.CharField(
        max_length=50,
        choices=[
            ('finance', 'Finance & Accounting'),
            ('customer_service', 'Customer Service'),
            ('sales', 'Sales & CRM'),
            ('general', 'General Purpose'),
            ('custom', 'Custom'),
        ]
    )

    graph_definition = models.JSONField(
        help_text="Graph structure in JSON format with nodes and edges"
    )

    default_config = models.JSONField(
        default=dict,
        help_text="Default configuration for this template (LLM, tools, prompts)"
    )

    is_global = models.BooleanField(
        default=False,
        help_text="If true, all organizations can use this template"
    )

    version = models.CharField(max_length=20, default="1.0.0")
    created_by = models.ForeignKey(
        OrganizationUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_templates"
    )

    class Meta:
        app_label = 'constec_db'
        db_table = 'constancia"."flow_templates'
        unique_together = [['organization', 'name', 'version']]
        indexes = [
            models.Index(fields=['organization', 'is_global']),
            models.Index(fields=['category', 'is_active']),
        ]

    def __str__(self):
        global_tag = " [GLOBAL]" if self.is_global else ""
        return f"{self.name} v{self.version}{global_tag}"


class Flow(UUIDModel):
    """Company-specific flow configuration.

    Can either use a template or define custom graph.
    Defines how the AI agent behaves for a specific company.
    """

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="flows",
    )

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    template = models.ForeignKey(
        FlowTemplate,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="flows",
        help_text="If set, uses template's graph. config overrides template defaults."
    )

    graph_definition = models.JSONField(
        null=True,
        blank=True,
        help_text="Custom graph structure (only if not using template)"
    )

    config = models.JSONField(
        default=dict,
        help_text="Configuration that merges with template.default_config"
    )

    is_default = models.BooleanField(
        default=False,
        help_text="Whether this is the default flow for the company"
    )

    class Meta:
        app_label = 'constec_db'
        db_table = 'constancia"."flows'
        unique_together = [['company', 'name']]
        indexes = [
            models.Index(fields=['company', 'is_default']),
            models.Index(fields=['template', 'is_active']),
        ]

    def get_graph_definition(self):
        """Returns the graph definition (from template or custom)."""
        if self.template:
            return self.template.graph_definition
        return self.graph_definition

    def get_merged_config(self):
        """Merges template defaults with flow config."""
        if self.template:
            merged = {**self.template.default_config}
            merged.update(self.config)
            return merged
        return self.config

    def __str__(self):
        default = " (Default)" if self.is_default else ""
        return f"{self.company.name} - {self.name}{default}"
