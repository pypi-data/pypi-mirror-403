"""Unit tests for Contact model."""

from datetime import UTC
from datetime import datetime
from unittest import mock

from amsdal_crm.models.contact import Contact


def test_contact_creation(unit_contact_data):
    """Test creating a contact."""
    contact = Contact(**unit_contact_data)

    assert contact.first_name == 'John'
    assert contact.last_name == 'Doe'
    assert contact.email == 'john.doe@example.com'
    assert contact.phone == '+1234567890'
    assert contact.mobile == '+0987654321'
    assert contact.title == 'CTO'
    assert contact.owner_email == 'test@example.com'


def test_contact_display_name(unit_contact_data):
    """Test contact display_name property."""
    contact = Contact(**unit_contact_data)

    assert contact.display_name == 'John Doe'


def test_contact_full_name(unit_contact_data):
    """Test contact full_name property."""
    contact = Contact(**unit_contact_data)

    assert contact.full_name == 'John Doe'


def test_contact_with_account(unit_user, unit_account_data):
    """Test contact linked to an account."""
    from datetime import UTC
    from datetime import datetime

    from amsdal_crm.models.account import Account

    account = Account(**unit_account_data)

    contact = Contact(
        first_name='Jane',
        last_name='Smith',
        email='jane@example.com',
        account=account,
        owner_email=unit_user.email,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert contact.account == account
    assert contact.account.name == 'ACME Corp'


def test_contact_without_account(unit_user):
    """Test contact without an account."""
    from datetime import UTC
    from datetime import datetime

    contact = Contact(
        first_name='John',
        last_name='Doe',
        email='john@example.com',
        owner_email=unit_user.email,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert contact.account is None


def test_contact_has_object_permission_owner(unit_user, unit_contact_data):
    """Test that owner has permission."""
    contact = Contact(**unit_contact_data)

    assert contact.has_object_permission(unit_user, 'read') is True
    assert contact.has_object_permission(unit_user, 'update') is True
    assert contact.has_object_permission(unit_user, 'delete') is True


def test_contact_has_object_permission_non_owner(unit_contact_data):
    """Test that non-owner doesn't have permission."""
    contact = Contact(**unit_contact_data)

    other_user = mock.Mock()
    other_user.email = 'other@example.com'
    other_user.permissions = []

    assert contact.has_object_permission(other_user, 'read') is False


def test_contact_has_object_permission_admin(unit_admin_user, unit_contact_data):
    """Test that admin has permission."""
    contact = Contact(**unit_contact_data)

    assert contact.has_object_permission(unit_admin_user, 'read') is True
    assert contact.has_object_permission(unit_admin_user, 'delete') is True


def test_contact_custom_fields(unit_user):
    """Test contact with custom fields."""
    from datetime import UTC
    from datetime import datetime

    contact = Contact(
        first_name='John',
        last_name='Doe',
        email='john@example.com',
        owner_email=unit_user.email,
        custom_fields={'customer_tier': 'gold', 'lead_source': 'Website'},
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert contact.custom_fields['customer_tier'] == 'gold'
    assert contact.custom_fields['lead_source'] == 'Website'


def test_contact_pre_update_sets_updated_at(unit_contact_data):
    """Test that pre_update sets updated_at timestamp."""
    contact = Contact(**unit_contact_data)
    contact.updated_at = None

    with mock.patch('amsdal_crm.services.custom_field_service.CustomFieldService'):
        contact.pre_update()

    assert contact.updated_at is not None
    assert isinstance(contact.updated_at, datetime)
    assert contact.updated_at.tzinfo == UTC


def test_contact_pre_create_validates_custom_fields(unit_user):
    """Test that pre_create validates custom fields."""
    contact = Contact(
        first_name='John',
        last_name='Doe',
        email='john@example.com',
        owner_email=unit_user.email,
        custom_fields={'test': 'value'},
    )

    with mock.patch('amsdal_crm.services.custom_field_service.CustomFieldService') as mock_service:
        mock_service.validate_custom_fields.return_value = {'test': 'validated_value'}

        contact.pre_create()

        mock_service.validate_custom_fields.assert_called_once_with('Contact', {'test': 'value'})
        assert contact.custom_fields == {'test': 'validated_value'}


def test_contact_post_update_executes_workflows(unit_contact_data):
    """Test that post_update executes workflow rules."""
    contact = Contact(**unit_contact_data)

    with mock.patch('amsdal_crm.services.workflow_service.WorkflowService') as mock_service:
        contact.post_update()

        mock_service.execute_rules.assert_called_once_with('Contact', 'update', contact)
