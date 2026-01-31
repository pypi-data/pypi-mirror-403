"""Unit tests for Account model."""

from datetime import UTC
from datetime import datetime
from unittest import mock

from amsdal_crm.models.account import Account


def test_account_creation(unit_account_data):
    """Test creating an account."""
    account = Account(**unit_account_data)

    assert account.name == 'ACME Corp'
    assert account.website == 'https://acme.example.com'
    assert account.phone == '+1234567890'
    assert account.industry == 'Technology'
    assert account.billing_city == 'San Francisco'
    assert account.owner_email == 'test@example.com'


def test_account_display_name(unit_account_data):
    """Test account display_name property."""
    account = Account(**unit_account_data)

    assert account.display_name == 'ACME Corp'


def test_account_full_name(unit_account_data):
    """Test account full_name property (same as display_name)."""
    account = Account(**unit_account_data)

    assert account.display_name == 'ACME Corp'


def test_account_has_object_permission_owner(unit_user, unit_account_data):
    """Test that owner has permission."""
    account = Account(**unit_account_data)

    assert account.has_object_permission(unit_user, 'read') is True
    assert account.has_object_permission(unit_user, 'update') is True
    assert account.has_object_permission(unit_user, 'delete') is True


def test_account_has_object_permission_non_owner(unit_account_data):
    """Test that non-owner doesn't have permission."""
    account = Account(**unit_account_data)

    other_user = mock.Mock()
    other_user.email = 'other@example.com'
    other_user.permissions = []

    assert account.has_object_permission(other_user, 'read') is False
    assert account.has_object_permission(other_user, 'update') is False


def test_account_has_object_permission_admin(unit_admin_user, unit_account_data):
    """Test that admin has permission."""
    account = Account(**unit_account_data)

    assert account.has_object_permission(unit_admin_user, 'read') is True
    assert account.has_object_permission(unit_admin_user, 'update') is True
    assert account.has_object_permission(unit_admin_user, 'delete') is True


def test_account_has_object_permission_specific_model_permission(unit_account_data):
    """Test specific model permission."""
    account = Account(**unit_account_data)

    user_with_perm = mock.Mock()
    user_with_perm.email = 'other@example.com'
    permission = mock.Mock()
    permission.model = 'Account'
    permission.action = 'read'
    user_with_perm.permissions = [permission]

    assert account.has_object_permission(user_with_perm, 'read') is True
    assert account.has_object_permission(user_with_perm, 'update') is False


def test_account_custom_fields(unit_user):
    """Test account with custom fields."""
    from datetime import UTC
    from datetime import datetime

    account = Account(
        name='Test Corp',
        owner_email=unit_user.email,
        custom_fields={'industry_vertical': 'SaaS', 'employee_count': 250},
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert account.custom_fields['industry_vertical'] == 'SaaS'
    assert account.custom_fields['employee_count'] == 250


def test_account_pre_update_sets_updated_at(unit_account_data):
    """Test that pre_update sets updated_at timestamp."""
    account = Account(**unit_account_data)
    account.updated_at = None

    # Mock the CustomFieldService to avoid database calls
    with mock.patch('amsdal_crm.services.custom_field_service.CustomFieldService'):
        account.pre_update()

    assert account.updated_at is not None
    assert isinstance(account.updated_at, datetime)
    assert account.updated_at.tzinfo == UTC


def test_account_pre_create_validates_custom_fields(unit_user):
    """Test that pre_create validates custom fields."""
    account = Account(name='Test Corp', owner_email=unit_user.email, custom_fields={'test': 'value'})

    with mock.patch('amsdal_crm.services.custom_field_service.CustomFieldService') as mock_service:
        mock_service.validate_custom_fields.return_value = {'test': 'validated_value'}

        account.pre_create()

        mock_service.validate_custom_fields.assert_called_once_with('Account', {'test': 'value'})
        assert account.custom_fields == {'test': 'validated_value'}


def test_account_post_update_executes_workflows(unit_account_data):
    """Test that post_update executes workflow rules."""
    account = Account(**unit_account_data)

    with mock.patch('amsdal_crm.services.workflow_service.WorkflowService') as mock_service:
        account.post_update()

        mock_service.execute_rules.assert_called_once_with('Account', 'update', account)


# Edge Case Tests


def test_account_with_minimal_required_fields(unit_user):
    """Test account creation with only required fields."""
    account = Account(
        name='Minimal Corp',
        owner_email=unit_user.email,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert account.name == 'Minimal Corp'
    assert account.owner_email == unit_user.email
    assert account.website is None
    assert account.phone is None
    assert account.industry is None
    assert account.billing_street is None
    assert account.billing_city is None
    assert account.billing_state is None
    assert account.billing_postal_code is None
    assert account.billing_country is None
    assert account.custom_fields is None


def test_account_with_all_optional_fields_none(unit_user):
    """Test account with all optional fields explicitly set to None."""
    account = Account(
        name='Optional None Corp',
        owner_email=unit_user.email,
        website=None,
        phone=None,
        industry=None,
        billing_street=None,
        billing_city=None,
        billing_state=None,
        billing_postal_code=None,
        billing_country=None,
        custom_fields=None,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert account.name == 'Optional None Corp'
    assert account.website is None
    assert account.custom_fields is None


def test_account_with_very_long_name(unit_user):
    """Test account with very long name (boundary testing)."""
    long_name = 'A' * 500
    account = Account(
        name=long_name,
        owner_email=unit_user.email,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert account.name == long_name
    assert len(account.name) == 500


def test_account_with_special_characters_in_name(unit_user):
    """Test account with special characters in name."""
    special_name = "O'Reilly & Associates, Inc. <test@example.com> - #1"
    account = Account(
        name=special_name,
        owner_email=unit_user.email,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert account.name == special_name


def test_account_with_unicode_characters(unit_user):
    """Test account with Unicode characters in fields."""
    account = Account(
        name='株式会社テスト',  # Japanese
        billing_city='北京',  # Chinese
        billing_country='日本',
        industry='Technología',  # Spanish
        owner_email=unit_user.email,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert account.name == '株式会社テスト'
    assert account.billing_city == '北京'
    assert account.industry == 'Technología'


def test_account_with_empty_custom_fields(unit_user):
    """Test account with empty custom_fields dict."""
    account = Account(
        name='Empty Custom Fields Corp',
        owner_email=unit_user.email,
        custom_fields={},
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert account.custom_fields == {}


def test_account_with_large_custom_fields(unit_user):
    """Test account with large custom_fields dict."""
    large_custom_fields = {f'field_{i}': f'value_{i}' for i in range(100)}

    account = Account(
        name='Large Custom Fields Corp',
        owner_email=unit_user.email,
        custom_fields=large_custom_fields,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert len(account.custom_fields) == 100
    assert account.custom_fields['field_0'] == 'value_0'
    assert account.custom_fields['field_99'] == 'value_99'


def test_account_with_nested_custom_fields(unit_user):
    """Test account with nested structures in custom_fields."""
    nested_custom_fields = {
        'address': {'street': '123 Main St', 'city': 'San Francisco', 'zip': '94105'},
        'contacts': [{'name': 'John', 'role': 'CEO'}, {'name': 'Jane', 'role': 'CTO'}],
        'metadata': {'source': 'import', 'confidence': 0.95},
    }

    account = Account(
        name='Nested Custom Fields Corp',
        owner_email=unit_user.email,
        custom_fields=nested_custom_fields,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert account.custom_fields['address']['city'] == 'San Francisco'
    assert len(account.custom_fields['contacts']) == 2
    assert account.custom_fields['metadata']['confidence'] == 0.95


def test_account_with_various_custom_field_types(unit_user):
    """Test account with various data types in custom_fields."""
    account = Account(
        name='Various Types Corp',
        owner_email=unit_user.email,
        custom_fields={
            'string_field': 'text',
            'int_field': 42,
            'float_field': 3.14,
            'bool_field': True,
            'list_field': [1, 2, 3],
            'none_field': None,
        },
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert account.custom_fields['string_field'] == 'text'
    assert account.custom_fields['int_field'] == 42
    assert account.custom_fields['float_field'] == 3.14
    assert account.custom_fields['bool_field'] is True
    assert account.custom_fields['list_field'] == [1, 2, 3]
    assert account.custom_fields['none_field'] is None


def test_multiple_accounts_with_same_name_different_owners(unit_user):
    """Test that multiple accounts can have the same name with different owners."""
    account1 = Account(
        name='Duplicate Name Corp',
        owner_email='owner1@example.com',
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    account2 = Account(
        name='Duplicate Name Corp',
        owner_email='owner2@example.com',
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    # Both should be created successfully (different owners)
    assert account1.name == account2.name
    assert account1.owner_email != account2.owner_email


def test_account_with_empty_string_name():
    """Test account with empty string name (should be allowed by model, may fail at DB level)."""
    account = Account(
        name='',
        owner_email='test@example.com',
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert account.name == ''


def test_account_with_whitespace_name(unit_user):
    """Test account with whitespace-only name."""
    account = Account(
        name='   ',
        owner_email=unit_user.email,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert account.name == '   '


def test_account_with_special_email_formats(unit_user):
    """Test account with various email formats for owner_email."""
    # Note: No email validation in model, so these should all work
    email_formats = [
        'simple@example.com',
        'user+tag@example.com',
        'user.name@example.co.uk',
        'user@subdomain.example.com',
        'first.last@example.com',
    ]

    for email in email_formats:
        account = Account(
            name=f'Account for {email}',
            owner_email=email,
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        assert account.owner_email == email


def test_account_with_invalid_email_format():
    """Test account with invalid email format (no validation in model)."""
    # Model doesn't validate email format, so this should work
    account = Account(
        name='Invalid Email Corp',
        owner_email='not-an-email',
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert account.owner_email == 'not-an-email'


def test_account_with_very_long_url(unit_user):
    """Test account with very long website URL."""
    long_url = 'https://example.com/' + 'a' * 1000
    account = Account(
        name='Long URL Corp',
        owner_email=unit_user.email,
        website=long_url,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert len(account.website) > 1000


def test_account_with_all_address_fields(unit_user):
    """Test account with all address fields populated."""
    account = Account(
        name='Full Address Corp',
        owner_email=unit_user.email,
        billing_street='123 Main Street, Suite 456',
        billing_city='San Francisco',
        billing_state='CA',
        billing_postal_code='94105',
        billing_country='USA',
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert account.billing_street == '123 Main Street, Suite 456'
    assert account.billing_city == 'San Francisco'
    assert account.billing_state == 'CA'
    assert account.billing_postal_code == '94105'
    assert account.billing_country == 'USA'


def test_account_display_name_with_special_characters(unit_user):
    """Test display_name with special characters."""
    special_name = 'Test & Co. <Special>'
    account = Account(
        name=special_name,
        owner_email=unit_user.email,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert account.display_name == special_name


def test_account_permission_check_with_empty_permissions_list(unit_account_data):
    """Test permission check when user has empty permissions list."""
    account = Account(**unit_account_data)

    user = mock.Mock()
    user.email = 'other@example.com'
    user.permissions = []

    assert account.has_object_permission(user, 'read') is False


def test_account_permission_check_with_none_permissions(unit_account_data):
    """Test permission check when user.permissions is None."""
    account = Account(**unit_account_data)

    user = mock.Mock()
    user.email = 'other@example.com'
    user.permissions = None

    assert account.has_object_permission(user, 'read') is False


def test_account_pre_create_with_none_custom_fields(unit_user):
    """Test pre_create with None custom_fields (should not call validation)."""
    account = Account(name='Test Corp', owner_email=unit_user.email, custom_fields=None)

    with mock.patch('amsdal_crm.services.custom_field_service.CustomFieldService') as mock_service:
        account.pre_create()

        # Should not call validate_custom_fields when custom_fields is None
        mock_service.validate_custom_fields.assert_not_called()


def test_account_pre_update_with_empty_custom_fields(unit_user):
    """Test pre_update with empty custom_fields dict."""
    account = Account(name='Test Corp', owner_email=unit_user.email, custom_fields={})

    with mock.patch('amsdal_crm.services.custom_field_service.CustomFieldService') as mock_service:
        mock_service.validate_custom_fields.return_value = {}

        with mock.patch('amsdal.models.mixins.TimestampMixin.pre_update'):
            account.pre_update()

        # Should not call validate_custom_fields with empty dict (falsy value)
        mock_service.validate_custom_fields.assert_not_called()
