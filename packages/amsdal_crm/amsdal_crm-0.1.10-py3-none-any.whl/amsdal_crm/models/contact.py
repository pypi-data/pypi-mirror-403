"""Contact Model."""

from typing import Any
from typing import ClassVar
from typing import Optional

from amsdal.contrib.auth.models.user import User
from amsdal.models.mixins import TimestampMixin
from amsdal_models.classes.data_models.constraints import UniqueConstraint
from amsdal_models.classes.data_models.indexes import IndexInfo
from amsdal_models.classes.model import Model
from amsdal_utils.models.enums import ModuleType
from pydantic.fields import Field


class Contact(TimestampMixin, Model):
    """Contact (Person) model.

    Represents a person in the CRM system, optionally linked to an Account.
    Owned by individual users with permission controls.
    """

    __module_type__: ClassVar[ModuleType] = ModuleType.CONTRIB
    __constraints__: ClassVar[list[UniqueConstraint]] = [UniqueConstraint(name='unq_contact_email', fields=['email'])]
    __indexes__: ClassVar[list[IndexInfo]] = [
        IndexInfo(name='idx_contact_owner_email', field='owner_email'),
        IndexInfo(name='idx_contact_created_at', field='created_at'),
    ]

    # Core fields
    first_name: str = Field(title='First Name')
    last_name: str = Field(title='Last Name')
    email: str = Field(title='Email')
    phone: str | None = Field(default=None, title='Phone Number')
    mobile: str | None = Field(default=None, title='Mobile Number')
    title: str | None = Field(default=None, title='Job Title')

    # Relationships
    account: Optional['Account'] = Field(default=None, title='Account')
    owner_email: str = Field(title='Owner Email')

    # Custom fields (JSON)
    custom_fields: dict[str, Any] | None = Field(default=None, title='Custom Fields')

    @property
    def display_name(self) -> str:
        """Return display name for the contact."""
        return f'{self.first_name} {self.last_name}'

    @property
    def full_name(self) -> str:
        """Return full name of the contact."""
        return f'{self.first_name} {self.last_name}'

    def has_object_permission(self, user: 'User', action: str) -> bool:
        """Check if user has permission to perform action on this contact.

        Args:
            user: The user attempting the action
            action: The action being attempted (read, create, update, delete)

        Returns:
            True if user has permission, False otherwise
        """
        # Owner has all permissions
        if self.owner_email == user.email:
            return True

        # Check admin permissions
        if user.permissions:
            for permission in user.permissions:
                if permission.model == '*' and permission.action in ('*', action):
                    return True
                if permission.model == 'Contact' and permission.action in ('*', action):
                    return True

        return False

    def pre_create(self) -> None:
        """Hook called before creating contact."""
        if self.custom_fields:
            from amsdal_crm.services.custom_field_service import CustomFieldService

            self.custom_fields = CustomFieldService.validate_custom_fields('Contact', self.custom_fields)
        super().pre_create()

    async def apre_create(self) -> None:
        """Async hook called before creating contact."""
        if self.custom_fields:
            from amsdal_crm.services.custom_field_service import CustomFieldService

            self.custom_fields = await CustomFieldService.avalidate_custom_fields('Contact', self.custom_fields)
        await super().apre_create()

    def pre_update(self) -> None:
        """Hook called before updating contact."""
        # Validate custom fields first
        if self.custom_fields:
            from amsdal_crm.services.custom_field_service import CustomFieldService

            self.custom_fields = CustomFieldService.validate_custom_fields('Contact', self.custom_fields)

        # Call parent to handle timestamps
        super().pre_update()

    async def apre_update(self) -> None:
        """Async hook called before updating contact."""
        # Validate custom fields first
        if self.custom_fields:
            from amsdal_crm.services.custom_field_service import CustomFieldService

            self.custom_fields = await CustomFieldService.avalidate_custom_fields('Contact', self.custom_fields)

        # Call parent to handle timestamps
        await super().apre_update()

    def post_update(self) -> None:
        """Hook called after updating contact."""
        from amsdal_crm.services.workflow_service import WorkflowService

        WorkflowService.execute_rules('Contact', 'update', self)

    async def apost_update(self) -> None:
        """Async hook called after updating contact."""
        from amsdal_crm.services.workflow_service import WorkflowService

        await WorkflowService.aexecute_rules('Contact', 'update', self)


from amsdal_crm.models.account import Account

Contact.model_rebuild()
