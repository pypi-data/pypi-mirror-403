"""Unit tests for Deal model."""

from datetime import UTC
from datetime import datetime
from decimal import Decimal
from unittest import mock

from amsdal_crm.models.deal import Deal


def test_deal_creation(unit_deal_data):
    """Test creating a deal."""
    deal = Deal(**unit_deal_data)

    assert deal.name == 'Enterprise Deal'
    assert deal.amount == Decimal('50000.00')
    assert deal.currency == 'USD'
    assert deal.owner_email == 'test@example.com'


def test_deal_display_name(unit_deal_data):
    """Test deal display_name property."""
    deal = Deal(**unit_deal_data)

    assert deal.display_name == 'Enterprise Deal'


def test_deal_stage_name_with_stage_object(unit_stage):
    """Test deal stage_name with stage object."""
    deal = Deal(
        name='Test Deal',
        stage=unit_stage,
        owner_email='test@example.com',
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert deal.stage_name == 'Qualified'


def test_deal_default_currency(unit_stage):
    """Test deal has default currency of USD."""
    deal = Deal(
        name='Test Deal',
        stage=unit_stage,
        owner_email='test@example.com',
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert deal.currency == 'USD'


def test_deal_default_status(unit_stage):
    """Test deal has default closed/won status as False."""
    deal = Deal(
        name='Test Deal',
        stage=unit_stage,
        owner_email='test@example.com',
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert deal.is_closed is False
    assert deal.is_won is False


def test_deal_has_object_permission_owner(unit_user, unit_deal_data):
    """Test that owner has permission."""
    deal = Deal(**unit_deal_data)

    assert deal.has_object_permission(unit_user, 'read') is True
    assert deal.has_object_permission(unit_user, 'update') is True
    assert deal.has_object_permission(unit_user, 'delete') is True


def test_deal_has_object_permission_non_owner(unit_deal_data):
    """Test that non-owner doesn't have permission."""
    deal = Deal(**unit_deal_data)

    other_user = mock.Mock()
    other_user.email = 'other@example.com'
    other_user.permissions = []

    assert deal.has_object_permission(other_user, 'read') is False


def test_deal_has_object_permission_admin(unit_admin_user, unit_deal_data):
    """Test that admin has permission."""
    deal = Deal(**unit_deal_data)

    assert deal.has_object_permission(unit_admin_user, 'read') is True
    assert deal.has_object_permission(unit_admin_user, 'update') is True


def test_deal_pre_update_syncs_closed_status_won(unit_pipeline):
    """Test that pre_update syncs is_closed and is_won with stage."""
    from amsdal_crm.models.stage import Stage

    stage = Stage(
        pipeline=unit_pipeline,
        name='Closed Won',
        order=5,
        probability=100.0,
        is_closed_won=True,
        is_closed_lost=False,
    )

    deal = Deal(
        name='Test Deal',
        stage=stage,
        owner_email='test@example.com',
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    with mock.patch('amsdal_crm.services.custom_field_service.CustomFieldService'):
        with mock.patch('amsdal_models.classes.helpers.reference_loader.ReferenceLoader') as mock_loader:
            mock_loader.return_value.load_reference.return_value = stage
            with mock.patch('amsdal.models.mixins.TimestampMixin.pre_update'):
                deal.pre_update()

    assert deal.is_closed is True
    assert deal.is_won is True
    assert deal.closed_date is not None


def test_deal_pre_update_syncs_closed_status_lost(unit_pipeline):
    """Test that pre_update syncs is_closed for lost deals."""
    from amsdal_crm.models.stage import Stage

    stage = Stage(
        pipeline=unit_pipeline,
        name='Closed Lost',
        order=6,
        probability=0.0,
        is_closed_won=False,
        is_closed_lost=True,
    )

    deal = Deal(
        name='Test Deal',
        stage=stage,
        owner_email='test@example.com',
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    with mock.patch('amsdal_crm.services.custom_field_service.CustomFieldService'):
        with mock.patch('amsdal_models.classes.helpers.reference_loader.ReferenceLoader') as mock_loader:
            mock_loader.return_value.load_reference.return_value = stage
            with mock.patch('amsdal.models.mixins.TimestampMixin.pre_update'):
                deal.pre_update()

    assert deal.is_closed is True
    assert deal.is_won is False
    assert deal.closed_date is not None


def test_deal_pre_update_doesnt_overwrite_closed_date(unit_pipeline):
    """Test that pre_update doesn't overwrite existing closed_date."""
    from amsdal_crm.models.stage import Stage

    stage = Stage(
        pipeline=unit_pipeline,
        name='Closed Won',
        order=5,
        probability=100.0,
        is_closed_won=True,
        is_closed_lost=False,
    )

    existing_closed_date = datetime(2026, 1, 1, tzinfo=UTC)
    deal = Deal(
        name='Test Deal',
        stage=stage,
        owner_email='test@example.com',
        closed_date=existing_closed_date,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    with mock.patch('amsdal_crm.services.custom_field_service.CustomFieldService'):
        with mock.patch('amsdal_models.classes.helpers.reference_loader.ReferenceLoader') as mock_loader:
            mock_loader.return_value.load_reference.return_value = stage
            with mock.patch('amsdal.models.mixins.TimestampMixin.pre_update'):
                deal.pre_update()

    assert deal.closed_date == existing_closed_date


def test_deal_pre_update_sets_updated_at(unit_stage):
    """Test that pre_update sets updated_at timestamp."""
    deal = Deal(
        name='Test Deal',
        stage=unit_stage,
        owner_email='test@example.com',
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    deal.updated_at = None

    with mock.patch('amsdal_crm.services.custom_field_service.CustomFieldService'):
        with mock.patch('amsdal_models.classes.helpers.reference_loader.ReferenceLoader') as mock_loader:
            mock_loader.return_value.load_reference.return_value = unit_stage
            with mock.patch('amsdal.models.mixins.TimestampMixin.pre_update') as mock_super:
                # Simulate the parent setting updated_at
                def set_updated_at():
                    deal.updated_at = datetime.now(UTC)

                mock_super.side_effect = set_updated_at

                deal.pre_update()

    assert deal.updated_at is not None
    assert isinstance(deal.updated_at, datetime)
    assert deal.updated_at.tzinfo == UTC


def test_deal_post_update_executes_workflows(unit_deal_data):
    """Test that post_update executes workflow rules."""
    deal = Deal(**unit_deal_data)

    with mock.patch('amsdal_crm.services.workflow_service.WorkflowService') as mock_service:
        deal.post_update()

        mock_service.execute_rules.assert_called_once_with('Deal', 'update', deal)


def test_deal_custom_fields(unit_user, unit_stage):
    """Test deal with custom fields."""
    deal = Deal(
        name='Test Deal',
        stage=unit_stage,
        owner_email=unit_user.email,
        custom_fields={'deal_source': 'Referral', 'commission_rate': 10},
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert deal.custom_fields['deal_source'] == 'Referral'
    assert deal.custom_fields['commission_rate'] == 10
