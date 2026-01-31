"""CRM Models."""

# Import File first for Attachment's forward reference
from amsdal.models.core.file import File  # noqa: F401

from amsdal_crm.models.account import Account
from amsdal_crm.models.activity import Activity
from amsdal_crm.models.activity import ActivityRelatedTo
from amsdal_crm.models.activity import ActivityType
from amsdal_crm.models.activity import Call
from amsdal_crm.models.activity import EmailActivity
from amsdal_crm.models.activity import Event
from amsdal_crm.models.activity import Note
from amsdal_crm.models.activity import Task
from amsdal_crm.models.attachment import Attachment
from amsdal_crm.models.contact import Contact
from amsdal_crm.models.custom_field_definition import CustomFieldDefinition
from amsdal_crm.models.deal import Deal
from amsdal_crm.models.pipeline import Pipeline
from amsdal_crm.models.stage import Stage
from amsdal_crm.models.workflow_rule import WorkflowRule

__all__ = [
    'Account',
    'Activity',
    'ActivityRelatedTo',
    'ActivityType',
    'Attachment',
    'Call',
    'Contact',
    'CustomFieldDefinition',
    'Deal',
    'EmailActivity',
    'Event',
    'Note',
    'Pipeline',
    'Stage',
    'Task',
    'WorkflowRule',
]

# Rebuild models to resolve forward references
Contact.model_rebuild()
Deal.model_rebuild()
Stage.model_rebuild()
Attachment.model_rebuild()
