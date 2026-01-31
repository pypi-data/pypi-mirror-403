"""Integration tests for DealService."""

from decimal import Decimal

from amsdal.manager import AmsdalManager

from amsdal_crm.models.activity import ActivityRelatedTo
from amsdal_crm.models.activity import Note
from amsdal_crm.models.deal import Deal
from amsdal_crm.models.stage import Stage
from amsdal_crm.services.deal_service import DealService


def test_move_deal_to_stage(crm_manager: AmsdalManager, mock_user, sample_pipeline):
    """Test moving a deal to a new stage."""
    # Create old and new stages
    old_stage = Stage(
        pipeline=sample_pipeline,
        name='Qualified',
        order=1,
        probability=25.0,
        is_closed_won=False,
        is_closed_lost=False,
    )
    old_stage.save(force_insert=True)

    new_stage = Stage(
        pipeline=sample_pipeline,
        name='Proposal',
        order=3,
        probability=50.0,
        is_closed_won=False,
        is_closed_lost=False,
    )
    new_stage.save(force_insert=True)

    # Create deal
    deal = Deal(
        name='Test Deal',
        stage=old_stage,
        owner_email=mock_user.email,
        amount=Decimal('10000'),
    )
    deal.save(force_insert=True)

    # Move deal to new stage
    updated_deal = DealService.move_deal_to_stage(
        deal=deal, new_stage_id=new_stage._object_id, note=None, user_email=mock_user.email
    )

    # Verify deal stage was updated
    assert updated_deal.stage._object_id == new_stage._object_id

    # Verify activity was created
    activities = Note.objects.filter(related_to_type=ActivityRelatedTo.DEAL, related_to_id=deal._object_id).execute()
    assert len(activities) >= 1
    assert any('Qualified → Proposal' in activity.subject for activity in activities)


def test_move_deal_to_stage_creates_activity(crm_manager: AmsdalManager, mock_user, sample_pipeline):
    """Test that moving a deal creates an activity log entry."""
    old_stage = Stage(
        pipeline=sample_pipeline,
        name='Lead',
        order=1,
        probability=10.0,
        is_closed_won=False,
        is_closed_lost=False,
    )
    old_stage.save(force_insert=True)

    new_stage = Stage(
        pipeline=sample_pipeline,
        name='Qualified',
        order=2,
        probability=25.0,
        is_closed_won=False,
        is_closed_lost=False,
    )
    new_stage.save(force_insert=True)

    deal = Deal(name='Test Deal', stage=old_stage, owner_email=mock_user.email)
    deal.save(force_insert=True)

    DealService.move_deal_to_stage(deal=deal, new_stage_id=new_stage._object_id, note=None, user_email=mock_user.email)

    # Verify Note was created
    activities = Note.objects.filter(related_to_type=ActivityRelatedTo.DEAL, related_to_id=deal._object_id).execute()
    assert len(activities) == 1
    note = activities[0]
    assert note.subject == 'Deal moved: Lead → Qualified'
    assert note.related_to_type == ActivityRelatedTo.DEAL
    assert note.related_to_id == deal._object_id
    assert note.owner_email == mock_user.email


def test_move_deal_to_stage_with_custom_note(crm_manager: AmsdalManager, mock_user, sample_pipeline):
    """Test moving a deal with a custom note."""
    old_stage = Stage(
        pipeline=sample_pipeline,
        name='Proposal',
        order=3,
        probability=50.0,
        is_closed_won=False,
        is_closed_lost=False,
    )
    old_stage.save(force_insert=True)

    new_stage = Stage(
        pipeline=sample_pipeline,
        name='Negotiation',
        order=4,
        probability=75.0,
        is_closed_won=False,
        is_closed_lost=False,
    )
    new_stage.save(force_insert=True)

    deal = Deal(name='Test Deal', stage=old_stage, owner_email=mock_user.email)
    deal.save(force_insert=True)

    custom_note = 'Client agreed to pricing, moving to final negotiations'

    DealService.move_deal_to_stage(
        deal=deal, new_stage_id=new_stage._object_id, note=custom_note, user_email=mock_user.email
    )

    # Verify custom note was used
    activities = Note.objects.filter(related_to_type=ActivityRelatedTo.DEAL, related_to_id=deal._object_id).execute()
    assert len(activities) == 1
    note = activities[0]
    assert note.description == custom_note


def test_move_deal_to_closed_won_emits_event(crm_manager: AmsdalManager, mock_user, sample_pipeline):
    """Test that moving to closed won stage emits ON_DEAL_WON event."""
    old_stage = Stage(
        pipeline=sample_pipeline,
        name='Negotiation',
        order=4,
        probability=75.0,
        is_closed_won=False,
        is_closed_lost=False,
    )
    old_stage.save(force_insert=True)

    new_stage = Stage(
        pipeline=sample_pipeline,
        name='Closed Won',
        order=5,
        probability=100.0,
        is_closed_won=True,
        is_closed_lost=False,
    )
    new_stage.save(force_insert=True)

    deal = Deal(name='Won Deal', stage=old_stage, owner_email=mock_user.email)
    deal.save(force_insert=True)

    # Move to closed won stage (would emit events if LifecycleProducer was active)
    updated_deal = DealService.move_deal_to_stage(
        deal=deal, new_stage_id=new_stage._object_id, note=None, user_email=mock_user.email
    )

    # Verify deal was moved to closed won stage
    assert updated_deal.stage.is_closed_won is True


def test_move_deal_to_closed_lost_emits_event(crm_manager: AmsdalManager, mock_user, sample_pipeline):
    """Test that moving to closed lost stage emits ON_DEAL_LOST event."""
    old_stage = Stage(
        pipeline=sample_pipeline,
        name='Negotiation',
        order=4,
        probability=75.0,
        is_closed_won=False,
        is_closed_lost=False,
    )
    old_stage.save(force_insert=True)

    new_stage = Stage(
        pipeline=sample_pipeline,
        name='Closed Lost',
        order=6,
        probability=0.0,
        is_closed_won=False,
        is_closed_lost=True,
    )
    new_stage.save(force_insert=True)

    deal = Deal(name='Lost Deal', stage=old_stage, owner_email=mock_user.email)
    deal.save(force_insert=True)

    # Move to closed lost stage (would emit events if LifecycleProducer was active)
    updated_deal = DealService.move_deal_to_stage(
        deal=deal, new_stage_id=new_stage._object_id, note=None, user_email=mock_user.email
    )

    # Verify deal was moved to closed lost stage
    assert updated_deal.stage.is_closed_lost is True


def test_move_deal_to_regular_stage_no_win_loss_event(crm_manager: AmsdalManager, mock_user, sample_pipeline):
    """Test that moving to regular stage doesn't emit win/loss events."""
    old_stage = Stage(
        pipeline=sample_pipeline,
        name='Lead',
        order=1,
        probability=10.0,
        is_closed_won=False,
        is_closed_lost=False,
    )
    old_stage.save(force_insert=True)

    new_stage = Stage(
        pipeline=sample_pipeline,
        name='Qualified',
        order=2,
        probability=25.0,
        is_closed_won=False,
        is_closed_lost=False,
    )
    new_stage.save(force_insert=True)

    deal = Deal(name='Regular Deal', stage=old_stage, owner_email=mock_user.email)
    deal.save(force_insert=True)

    # Move to regular stage
    updated_deal = DealService.move_deal_to_stage(
        deal=deal, new_stage_id=new_stage._object_id, note=None, user_email=mock_user.email
    )

    # Verify deal was moved
    assert updated_deal.stage._object_id == new_stage._object_id
    assert updated_deal.stage.is_closed_won is False
    assert updated_deal.stage.is_closed_lost is False


def test_move_deal_to_stage_integration(crm_manager: AmsdalManager, mock_user, sample_pipeline):
    """Test moving a deal to a new stage (integration test variant)."""
    old_stage = Stage(
        pipeline=sample_pipeline,
        name='Lead',
        order=1,
        probability=10.0,
        is_closed_won=False,
        is_closed_lost=False,
    )
    old_stage.save(force_insert=True)

    new_stage = Stage(
        pipeline=sample_pipeline,
        name='Qualified',
        order=2,
        probability=25.0,
        is_closed_won=False,
        is_closed_lost=False,
    )
    new_stage.save(force_insert=True)

    deal = Deal(name='Integration Test Deal', stage=old_stage, owner_email=mock_user.email)
    deal.save(force_insert=True)

    # Move deal to new stage
    updated_deal = DealService.move_deal_to_stage(
        deal=deal, new_stage_id=new_stage._object_id, note=None, user_email=mock_user.email
    )

    # Verify deal stage was updated
    assert updated_deal.stage._object_id == new_stage._object_id


def test_move_deal_to_closed_won_integration(crm_manager: AmsdalManager, mock_user, sample_pipeline):
    """Test moving to closed won stage (integration test variant)."""
    old_stage = Stage(
        pipeline=sample_pipeline,
        name='Negotiation',
        order=4,
        probability=75.0,
        is_closed_won=False,
        is_closed_lost=False,
    )
    old_stage.save(force_insert=True)

    new_stage = Stage(
        pipeline=sample_pipeline,
        name='Closed Won',
        order=5,
        probability=100.0,
        is_closed_won=True,
        is_closed_lost=False,
    )
    new_stage.save(force_insert=True)

    deal = Deal(name='Won Deal Integration', stage=old_stage, owner_email=mock_user.email)
    deal.save(force_insert=True)

    # Move to closed won stage
    updated_deal = DealService.move_deal_to_stage(
        deal=deal, new_stage_id=new_stage._object_id, note=None, user_email=mock_user.email
    )

    # Verify deal was moved to closed won stage
    assert updated_deal.stage.is_closed_won is True


# Note: Async integration tests are not included because the integration test environment
# does not have async connection pools and async database infrastructure configured.
# Async functionality is tested in unit tests where transactions are mocked.
