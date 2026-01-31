"""Unit tests for Stage model."""

from amsdal_crm.models.stage import Stage


def test_stage_creation(sample_stage_data):
    """Test creating a stage."""
    stage = Stage(**sample_stage_data)

    assert stage.name == 'Qualified'
    assert stage.order == 2
    assert stage.probability == 25.0
    assert stage.is_closed_won is False
    assert stage.is_closed_lost is False


def test_stage_display_name_with_pipeline_object(unit_pipeline):
    """Test stage display_name with pipeline object."""
    stage = Stage(
        pipeline=unit_pipeline,
        name='Qualified',
        order=2,
        probability=25.0,
    )

    assert stage.display_name == 'Test Pipeline - Qualified'


def test_stage_closed_won(unit_pipeline):
    """Test creating a closed won stage."""
    stage = Stage(
        pipeline=unit_pipeline,
        name='Closed Won',
        order=5,
        probability=100.0,
        is_closed_won=True,
        is_closed_lost=False,
    )

    assert stage.is_closed_won is True
    assert stage.is_closed_lost is False


def test_stage_closed_lost(unit_pipeline):
    """Test creating a closed lost stage."""
    stage = Stage(
        pipeline=unit_pipeline,
        name='Closed Lost',
        order=6,
        probability=0.0,
        is_closed_won=False,
        is_closed_lost=True,
    )

    assert stage.is_closed_won is False
    assert stage.is_closed_lost is True
