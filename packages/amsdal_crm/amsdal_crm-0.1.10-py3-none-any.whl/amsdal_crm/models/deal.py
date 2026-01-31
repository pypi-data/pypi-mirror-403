"""Deal Model."""

import datetime as _dt
from typing import Any
from typing import ClassVar
from typing import Optional

from amsdal.contrib.auth.models.user import User
from amsdal.models.mixins import TimestampMixin
from amsdal_models.classes.data_models.indexes import IndexInfo
from amsdal_models.classes.model import Model
from amsdal_models.managers.model_manager import Manager
from amsdal_utils.models.data_models.reference import Reference
from amsdal_utils.models.enums import ModuleType
from pydantic.fields import Field


class DealManager(Manager):
    def get_queryset(self) -> 'DealManager':
        return super().get_queryset().select_related('stage')


class Deal(TimestampMixin, Model):
    """Deal (Sales Opportunity) model.

    Represents a sales opportunity linked to an account and contact,
    progressing through pipeline stages.
    """

    __module_type__: ClassVar[ModuleType] = ModuleType.CONTRIB
    __indexes__: ClassVar[list[IndexInfo]] = [
        IndexInfo(name='idx_deal_owner_email', field='owner_email'),
        IndexInfo(name='idx_deal_close_date', field='expected_close_date'),
        IndexInfo(name='idx_deal_created_at', field='created_at'),
    ]

    # Core fields
    name: str = Field(title='Deal Name')
    amount: float | None = Field(default=None, title='Amount', ge=0)
    currency: str = Field(default='USD', title='Currency')

    # Relationships
    account: Optional['Account'] = Field(default=None, title='Account')
    contact: Optional['Contact'] = Field(default=None, title='Primary Contact')
    stage: 'Stage' = Field(title='Stage')
    owner_email: str = Field(title='Owner Email')

    # Dates
    expected_close_date: _dt.datetime | None = Field(default=None, title='Expected Close Date')
    closed_date: _dt.datetime | None = Field(default=None, title='Closed Date')

    # Status tracking
    is_closed: bool = Field(default=False, title='Is Closed')
    is_won: bool = Field(default=False, title='Is Won')

    # Custom fields (JSON)
    custom_fields: dict[str, Any] | None = Field(default=None, title='Custom Fields')

    @property
    def display_name(self) -> str:
        """Return display name for the deal."""
        return self.name

    @property
    def stage_name(self) -> str:
        """Returns stage name for display."""
        if hasattr(self.stage, 'name'):
            return self.stage.name
        return str(self.stage)

    def has_object_permission(self, user: 'User', action: str) -> bool:
        """Check if user has permission to perform action on this deal.

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
                if permission.model == 'Deal' and permission.action in ('*', action):
                    return True

        return False

    def pre_create(self) -> None:
        """Hook called before creating deal."""
        if self.custom_fields:
            from amsdal_crm.services.custom_field_service import CustomFieldService

            self.custom_fields = CustomFieldService.validate_custom_fields('Deal', self.custom_fields)
        super().pre_create()

    async def apre_create(self) -> None:
        """Async hook called before creating deal."""
        if self.custom_fields:
            from amsdal_crm.services.custom_field_service import CustomFieldService

            self.custom_fields = await CustomFieldService.avalidate_custom_fields('Deal', self.custom_fields)
        await super().apre_create()

    def pre_update(self) -> None:
        """Hook called before updating deal.

        Automatically syncs is_closed and is_won status with stage,
        and sets closed_date when deal is closed.
        """
        # Validate custom fields first
        if self.custom_fields:
            from amsdal_crm.services.custom_field_service import CustomFieldService

            self.custom_fields = CustomFieldService.validate_custom_fields('Deal', self.custom_fields)

        # Load stage if it's a reference and sync closed status
        from amsdal_models.classes.helpers.reference_loader import ReferenceLoader

        stage = ReferenceLoader(self.stage).load_reference() if isinstance(self.stage, Reference) else self.stage
        self.is_closed = stage.is_closed_won or stage.is_closed_lost
        self.is_won = stage.is_closed_won

        if self.is_closed and not self.closed_date:
            self.closed_date = _dt.datetime.now(_dt.UTC)

        # Call parent to handle timestamps
        super().pre_update()

    async def apre_update(self) -> None:
        """Async hook called before updating deal.

        Automatically syncs is_closed and is_won status with stage,
        and sets closed_date when deal is closed.
        """
        # Validate custom fields first
        if self.custom_fields:
            from amsdal_crm.services.custom_field_service import CustomFieldService

            self.custom_fields = await CustomFieldService.avalidate_custom_fields('Deal', self.custom_fields)

        # Load stage if it's a reference and sync closed status

        stage = await self.stage
        self.is_closed = stage.is_closed_won or stage.is_closed_lost
        self.is_won = stage.is_closed_won

        if self.is_closed and not self.closed_date:
            self.closed_date = _dt.datetime.now(_dt.UTC)

        # Call parent to handle timestamps
        await super().apre_update()

    def post_update(self) -> None:
        """Hook called after updating deal."""
        from amsdal_crm.services.workflow_service import WorkflowService

        WorkflowService.execute_rules('Deal', 'update', self)

    async def apost_update(self) -> None:
        """Async hook called after updating deal."""
        from amsdal_crm.services.workflow_service import WorkflowService

        await WorkflowService.aexecute_rules('Deal', 'update', self)


from amsdal_crm.models.account import Account
from amsdal_crm.models.contact import Contact
from amsdal_crm.models.stage import Stage

Deal.model_rebuild()
