"""Account Model."""

from typing import Any
from typing import ClassVar

from amsdal.contrib.auth.models.user import User
from amsdal.models.mixins import TimestampMixin
from amsdal_models.classes.data_models.constraints import UniqueConstraint
from amsdal_models.classes.data_models.indexes import IndexInfo
from amsdal_models.classes.model import Model
from amsdal_utils.models.enums import ModuleType
from pydantic.fields import Field


class Account(TimestampMixin, Model):
    """Account (Company/Organization) model.

    Represents a company or organization in the CRM system.
    Owned by individual users with permission controls.
    """

    __module_type__: ClassVar[ModuleType] = ModuleType.CONTRIB
    __constraints__: ClassVar[list[UniqueConstraint]] = [
        UniqueConstraint(name='unq_account_name_owner', fields=['name', 'owner_email'])
    ]
    __indexes__: ClassVar[list[IndexInfo]] = [
        IndexInfo(name='idx_account_owner_email', field='owner_email'),
        IndexInfo(name='idx_account_created_at', field='created_at'),
    ]

    # Core fields
    name: str = Field(title='Account Name')
    website: str | None = Field(default=None, title='Website')
    phone: str | None = Field(default=None, title='Phone')
    industry: str | None = Field(default=None, title='Industry')

    # Address fields
    billing_street: str | None = Field(default=None, title='Billing Street')
    billing_city: str | None = Field(default=None, title='Billing City')
    billing_state: str | None = Field(default=None, title='Billing State')
    billing_postal_code: str | None = Field(default=None, title='Billing Postal Code')
    billing_country: str | None = Field(default=None, title='Billing Country')

    # Ownership
    owner_email: str = Field(title='Owner Email')

    # Custom fields (JSON)
    custom_fields: dict[str, Any] | None = Field(default=None, title='Custom Fields')

    @property
    def display_name(self) -> str:
        """Return display name for the account."""
        return self.name

    def has_object_permission(self, user: 'User', action: str) -> bool:
        """Check if user has permission to perform action on this account.

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
                if permission.model == 'Account' and permission.action in ('*', action):
                    return True

        return False

    def pre_create(self) -> None:
        """Hook called before creating account."""
        if self.custom_fields:
            from amsdal_crm.services.custom_field_service import CustomFieldService

            self.custom_fields = CustomFieldService.validate_custom_fields('Account', self.custom_fields)
        super().pre_create()

    async def apre_create(self) -> None:
        """Async hook called before creating account."""
        if self.custom_fields:
            from amsdal_crm.services.custom_field_service import CustomFieldService

            self.custom_fields = await CustomFieldService.avalidate_custom_fields('Account', self.custom_fields)
        await super().apre_create()

    def pre_update(self) -> None:
        """Hook called before updating account."""
        # Validate custom fields first
        if self.custom_fields:
            from amsdal_crm.services.custom_field_service import CustomFieldService

            self.custom_fields = CustomFieldService.validate_custom_fields('Account', self.custom_fields)

        # Call parent to handle timestamps
        super().pre_update()

    async def apre_update(self) -> None:
        """Async hook called before updating account."""
        # Validate custom fields first
        if self.custom_fields:
            from amsdal_crm.services.custom_field_service import CustomFieldService

            self.custom_fields = await CustomFieldService.avalidate_custom_fields('Account', self.custom_fields)

        # Call parent to handle timestamps
        await super().apre_update()

    def post_update(self) -> None:
        """Hook called after updating account."""
        from amsdal_crm.services.workflow_service import WorkflowService

        WorkflowService.execute_rules('Account', 'update', self)

    async def apost_update(self) -> None:
        """Async hook called after updating account."""
        from amsdal_crm.services.workflow_service import WorkflowService

        await WorkflowService.aexecute_rules('Account', 'update', self)
