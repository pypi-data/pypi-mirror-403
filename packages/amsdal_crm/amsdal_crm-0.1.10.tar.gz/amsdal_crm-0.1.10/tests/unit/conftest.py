"""Test fixtures for CRM unit tests."""

from datetime import UTC
from datetime import datetime
from decimal import Decimal
from unittest import mock

import pytest

from amsdal_crm.models.pipeline import Pipeline
from amsdal_crm.models.stage import Stage


@pytest.fixture(scope='module')
def _init_config():
    """Initialize AmsdalConfigManager for all CRM unit tests."""
    from amsdal_utils.config.manager import AmsdalConfigManager

    # Create a mock config object
    mock_config = mock.Mock()
    mock_config.async_mode = False

    # Patch AmsdalConfigManager.get_config to return our mock config
    patcher = mock.patch.object(AmsdalConfigManager, 'get_config', return_value=mock_config)
    patcher.start()

    yield mock_config

    patcher.stop()


@pytest.fixture(scope='module')
def _mock_transaction_flow():
    """Mock TransactionFlow to avoid database transaction requirements."""

    # Create a mock context manager that does nothing
    class MockTransactionFlow:
        def __init__(self, func, *args, **kwargs):
            self.func = func
            self.args = args
            self.kwargs = kwargs
            self.return_value = None

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            return False

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            return False

        def set_return_value(self, value):
            """Set the return value (called by decorator)."""
            self.return_value = value

        def run(self):
            """Run the function without transaction."""
            return self.func(*self.args, **self.kwargs)

        async def arun(self):
            """Run the async function without transaction."""
            return await self.func(*self.args, **self.kwargs)

    patcher = mock.patch('amsdal_data.transactions.decorators.TransactionFlow', MockTransactionFlow)
    patcher.start()

    yield

    patcher.stop()


# Apply mocks automatically for all unit tests in this directory
@pytest.fixture(autouse=True, scope='module')
def _apply_unit_test_mocks(_init_config, _mock_transaction_flow):
    """Auto-apply unit test mocks for all tests in this package."""
    pass


@pytest.fixture
def unit_user():
    """Create a mock user for unit testing."""
    user = mock.Mock()
    user.email = 'test@example.com'
    user.permissions = []
    return user


@pytest.fixture
def unit_admin_user():
    """Create a mock admin user for unit testing."""
    user = mock.Mock()
    user.email = 'admin@example.com'
    permission = mock.Mock()
    permission.model = '*'
    permission.action = '*'
    user.permissions = [permission]
    return user


@pytest.fixture
def sample_pipeline_data():
    """Sample pipeline data for testing."""
    return {
        'name': 'Test Pipeline',
        'description': 'A test sales pipeline',
        'is_active': True,
    }


@pytest.fixture
def unit_pipeline():
    """Create a sample pipeline object for unit testing (no DB)."""
    return Pipeline(
        name='Test Pipeline',
        description='A test sales pipeline',
        is_active=True,
    )


@pytest.fixture
def unit_stage(unit_pipeline):
    """Create a sample stage object for unit testing (no DB)."""
    return Stage(
        pipeline=unit_pipeline,
        name='Qualified',
        order=2,
        probability=25.0,
        is_closed_won=False,
        is_closed_lost=False,
    )


@pytest.fixture
def sample_stage_data(unit_pipeline):
    """Sample stage data for testing."""
    return {
        'pipeline': unit_pipeline,
        'name': 'Qualified',
        'order': 2,
        'probability': 25.0,
        'is_closed_won': False,
        'is_closed_lost': False,
    }


@pytest.fixture
def unit_account_data(unit_user):
    """Sample account data for unit testing."""
    return {
        'name': 'ACME Corp',
        'website': 'https://acme.example.com',
        'phone': '+1234567890',
        'industry': 'Technology',
        'billing_street': '123 Main St',
        'billing_city': 'San Francisco',
        'billing_state': 'CA',
        'billing_postal_code': '94105',
        'billing_country': 'USA',
        'owner_email': unit_user.email,
        'created_at': datetime(2026, 1, 1, tzinfo=UTC),
    }


@pytest.fixture
def unit_contact_data(unit_user):
    """Sample contact data for unit testing."""
    return {
        'first_name': 'John',
        'last_name': 'Doe',
        'email': 'john.doe@example.com',
        'phone': '+1234567890',
        'mobile': '+0987654321',
        'title': 'CTO',
        'owner_email': unit_user.email,
        'created_at': datetime(2026, 1, 1, tzinfo=UTC),
    }


@pytest.fixture
def unit_deal_data(unit_user, unit_stage):
    """Sample deal data for unit testing."""
    return {
        'name': 'Enterprise Deal',
        'amount': Decimal('50000.00'),
        'currency': 'USD',
        'stage': unit_stage,
        'owner_email': unit_user.email,
        'expected_close_date': datetime(2026, 6, 1, tzinfo=UTC),
        'created_at': datetime(2026, 1, 1, tzinfo=UTC),
    }


@pytest.fixture
def sample_custom_field_definition_data():
    """Sample custom field definition data for testing."""
    return {
        'entity_type': 'Contact',
        'field_name': 'customer_tier',
        'field_label': 'Customer Tier',
        'field_type': 'choice',
        'choices': ['bronze', 'silver', 'gold', 'platinum'],
        'is_required': False,
        'display_order': 1,
    }


@pytest.fixture
def sample_workflow_rule_data():
    """Sample workflow rule data for testing."""
    return {
        'name': 'Notify on High Value Deal',
        'entity_type': 'Deal',
        'trigger_event': 'update',
        'condition_field': 'amount',
        'condition_operator': 'greater_than',
        'condition_value': Decimal('100000.00'),
        'action_type': 'create_activity',
        'action_config': {
            'subject': 'High value deal updated',
            'description': 'A high value deal was updated',
        },
        'is_active': True,
    }
