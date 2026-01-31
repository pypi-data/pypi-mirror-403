from django.db import models
from .base import UUIDModel
from .company import Company
from .person import Person
from .flow import Flow


class Session(UUIDModel):
    """Conversation session between a user and the AI agent.

    Tracks the conversation context including company, user, and permissions.
    All MCP tools receive the session_id to know who is making the request.
    """

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="sessions",
        help_text="The company this session belongs to"
    )
    user = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name="sessions",
        help_text="The person chatting (can be employee or client)"
    )
    flow = models.ForeignKey(
        Flow,
        on_delete=models.PROTECT,
        related_name="sessions",
        help_text="AI flow configuration to use"
    )

    metadata = models.JSONField(
        default=dict,
        help_text="Session context (connection, role, etc.)"
    )

    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = 'constec_db'
        db_table = 'constancia"."sessions'
        indexes = [
            models.Index(fields=['company', 'is_active']),
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"Session {self.id} - {self.user} @ {self.company.name}"


class Message(UUIDModel):
    """Message in a conversation session.

    Stores the conversation history between user and AI assistant.
    """

    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
    ]

    session = models.ForeignKey(
        Session,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()

    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional message data: tool calls, errors, context, etc."
    )

    class Meta:
        app_label = 'constec_db'
        db_table = 'constancia"."messages'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['session', 'created_at']),
        ]

    def __str__(self):
        preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"{self.role}: {preview}"
