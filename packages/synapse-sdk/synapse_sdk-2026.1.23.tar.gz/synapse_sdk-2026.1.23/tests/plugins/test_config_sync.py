"""Tests for config_sync module."""

from pydantic import BaseModel, Field

from synapse_sdk.plugins.config_sync import (
    ConfigSyncer,
    EntrypointSyncer,
    HyperparametersSyncer,
    MethodSyncer,
    TypesSyncer,
    get_default_syncers,
    sync_action_config,
)

# =============================================================================
# Test Fixtures
# =============================================================================


class SimpleParams(BaseModel):
    """Simple params model for testing."""

    epochs: int = Field(default=50, ge=1, le=1000, description='Number of epochs')
    batch_size: int = Field(default=8, ge=1, le=512, description='Batch size')
    learning_rate: float = Field(default=0.001, description='Learning rate')


class ParamsWithExclusions(BaseModel):
    """Params model with fields that should be excluded."""

    data_path: str = Field(description='Dataset path')  # Auto-excluded
    checkpoint: int | None = Field(default=None)  # Auto-excluded
    epochs: int = Field(default=50, ge=1)
    custom_excluded: str = Field(
        default='test',
        json_schema_extra={'hyperparameter': False},
    )
    ui_excluded: bool = Field(
        default=True,
        json_schema_extra={'exclude_from_ui': True},
    )


class ParamsWithCustomUI(BaseModel):
    """Params model with custom UI overrides."""

    image_size: int = Field(
        default=640,
        description='Image size',
        json_schema_extra={
            'formkit': 'radio',
            'options': [320, 416, 512, 640],
        },
    )
    momentum: float = Field(
        default=0.9,
        ge=0.0,
        le=1.0,
        description='Momentum',
        json_schema_extra={'step': 0.01},
    )


# =============================================================================
# EntrypointSyncer Tests
# =============================================================================


class TestEntrypointSyncer:
    """Tests for EntrypointSyncer."""

    def test_syncs_new_entrypoint(self):
        """Should add entrypoint when not present."""
        syncer = EntrypointSyncer()
        action_info = {'entrypoint': 'plugin.train.TrainAction'}
        action_config: dict = {}

        changes = syncer.sync('train', action_info, action_config)

        assert action_config['entrypoint'] == 'plugin.train.TrainAction'
        assert changes == ['entrypoint=plugin.train.TrainAction']

    def test_syncs_changed_entrypoint(self):
        """Should update entrypoint when different."""
        syncer = EntrypointSyncer()
        action_info = {'entrypoint': 'plugin.train.NewTrainAction'}
        action_config = {'entrypoint': 'plugin.train.OldTrainAction'}

        changes = syncer.sync('train', action_info, action_config)

        assert action_config['entrypoint'] == 'plugin.train.NewTrainAction'
        assert changes == ['entrypoint=plugin.train.NewTrainAction']

    def test_no_change_when_same(self):
        """Should not report change when entrypoint is same."""
        syncer = EntrypointSyncer()
        action_info = {'entrypoint': 'plugin.train.TrainAction'}
        action_config = {'entrypoint': 'plugin.train.TrainAction'}

        changes = syncer.sync('train', action_info, action_config)

        assert changes == []

    def test_no_change_when_missing_from_info(self):
        """Should not change anything when entrypoint not in action_info."""
        syncer = EntrypointSyncer()
        action_info: dict = {}
        action_config = {'entrypoint': 'plugin.train.TrainAction'}

        changes = syncer.sync('train', action_info, action_config)

        assert action_config['entrypoint'] == 'plugin.train.TrainAction'
        assert changes == []


# =============================================================================
# TypesSyncer Tests
# =============================================================================


class TestTypesSyncer:
    """Tests for TypesSyncer."""

    def test_syncs_input_type(self):
        """Should sync input_type."""
        syncer = TypesSyncer()
        action_info = {'input_type': 'yolo_dataset'}
        action_config: dict = {}

        changes = syncer.sync('train', action_info, action_config)

        assert action_config['input_type'] == 'yolo_dataset'
        assert 'input_type=yolo_dataset' in changes

    def test_syncs_output_type(self):
        """Should sync output_type."""
        syncer = TypesSyncer()
        action_info = {'output_type': 'model_weights'}
        action_config: dict = {}

        changes = syncer.sync('train', action_info, action_config)

        assert action_config['output_type'] == 'model_weights'
        assert 'output_type=model_weights' in changes

    def test_syncs_both_types(self):
        """Should sync both input and output types."""
        syncer = TypesSyncer()
        action_info = {'input_type': 'yolo_dataset', 'output_type': 'model_weights'}
        action_config: dict = {}

        changes = syncer.sync('train', action_info, action_config)

        assert action_config['input_type'] == 'yolo_dataset'
        assert action_config['output_type'] == 'model_weights'
        assert len(changes) == 2

    def test_no_change_when_same(self):
        """Should not report change when types are same."""
        syncer = TypesSyncer()
        action_info = {'input_type': 'yolo_dataset', 'output_type': 'model_weights'}
        action_config = {'input_type': 'yolo_dataset', 'output_type': 'model_weights'}

        changes = syncer.sync('train', action_info, action_config)

        assert changes == []

    def test_no_change_when_none(self):
        """Should not add types when None in action_info."""
        syncer = TypesSyncer()
        action_info = {'input_type': None, 'output_type': None}
        action_config: dict = {}

        changes = syncer.sync('train', action_info, action_config)

        assert 'input_type' not in action_config
        assert 'output_type' not in action_config
        assert changes == []


# =============================================================================
# HyperparametersSyncer Tests
# =============================================================================


class TestHyperparametersSyncer:
    """Tests for HyperparametersSyncer."""

    def test_generates_schema_for_train_action(self):
        """Should generate hyperparameters for train action."""
        syncer = HyperparametersSyncer()
        action_info = {'params_model': SimpleParams}
        action_config: dict = {}

        changes = syncer.sync('train', action_info, action_config)

        assert 'hyperparameters' in action_config
        assert 'train_ui_schemas' in action_config['hyperparameters']
        schema = action_config['hyperparameters']['train_ui_schemas']
        assert len(schema) == 3  # epochs, batch_size, learning_rate
        assert len(changes) == 1

    def test_generates_schema_for_tune_action(self):
        """Should generate hyperparameters for tune action."""
        syncer = HyperparametersSyncer()
        action_info = {'params_model': SimpleParams}
        action_config: dict = {}

        changes = syncer.sync('tune', action_info, action_config)

        assert 'hyperparameters' in action_config
        assert len(changes) == 1

    def test_skips_non_supported_actions(self):
        """Should not generate hyperparameters for unsupported actions."""
        syncer = HyperparametersSyncer()
        action_info = {'params_model': SimpleParams}

        for action_name in ['download', 'convert', 'test', 'inference', 'export']:
            action_config: dict = {}
            changes = syncer.sync(action_name, action_info, action_config)

            assert 'hyperparameters' not in action_config
            assert changes == []

    def test_skips_when_no_params_model(self):
        """Should not generate when params_model is None."""
        syncer = HyperparametersSyncer()
        action_info = {'params_model': None}
        action_config: dict = {}

        changes = syncer.sync('train', action_info, action_config)

        assert 'hyperparameters' not in action_config
        assert changes == []

    def test_excludes_default_fields(self):
        """Should exclude fields in DEFAULT_EXCLUDED_FIELDS."""
        syncer = HyperparametersSyncer()
        action_info = {'params_model': ParamsWithExclusions}
        action_config: dict = {}

        syncer.sync('train', action_info, action_config)

        schema = action_config['hyperparameters']['train_ui_schemas']
        field_names = [item['name'] for item in schema]

        assert 'data_path' not in field_names
        assert 'checkpoint' not in field_names
        assert 'epochs' in field_names

    def test_excludes_fields_with_hyperparameter_false(self):
        """Should exclude fields with json_schema_extra hyperparameter=False."""
        syncer = HyperparametersSyncer()
        action_info = {'params_model': ParamsWithExclusions}
        action_config: dict = {}

        syncer.sync('train', action_info, action_config)

        schema = action_config['hyperparameters']['train_ui_schemas']
        field_names = [item['name'] for item in schema]

        assert 'custom_excluded' not in field_names

    def test_excludes_fields_with_exclude_from_ui(self):
        """Should exclude fields with json_schema_extra exclude_from_ui=True."""
        syncer = HyperparametersSyncer()
        action_info = {'params_model': ParamsWithExclusions}
        action_config: dict = {}

        syncer.sync('train', action_info, action_config)

        schema = action_config['hyperparameters']['train_ui_schemas']
        field_names = [item['name'] for item in schema]

        assert 'ui_excluded' not in field_names

    def test_adds_required_to_all_fields(self):
        """Should add required=True to all hyperparameter fields."""
        syncer = HyperparametersSyncer()
        action_info = {'params_model': SimpleParams}
        action_config: dict = {}

        syncer.sync('train', action_info, action_config)

        schema = action_config['hyperparameters']['train_ui_schemas']
        for item in schema:
            assert item.get('required') is True

    def test_generates_correct_formkit_types(self):
        """Should generate correct FormKit types from Pydantic types."""
        syncer = HyperparametersSyncer()
        action_info = {'params_model': SimpleParams}
        action_config: dict = {}

        syncer.sync('train', action_info, action_config)

        schema = action_config['hyperparameters']['train_ui_schemas']
        schema_dict = {item['name']: item for item in schema}

        # int -> number
        assert schema_dict['epochs']['$formkit'] == 'number'
        assert schema_dict['epochs']['number'] is True

        # float -> number
        assert schema_dict['learning_rate']['$formkit'] == 'number'
        assert schema_dict['learning_rate']['number'] is True

    def test_generates_constraints(self):
        """Should generate min/max from Pydantic constraints."""
        syncer = HyperparametersSyncer()
        action_info = {'params_model': SimpleParams}
        action_config: dict = {}

        syncer.sync('train', action_info, action_config)

        schema = action_config['hyperparameters']['train_ui_schemas']
        schema_dict = {item['name']: item for item in schema}

        assert schema_dict['epochs']['min'] == 1
        assert schema_dict['epochs']['max'] == 1000
        assert schema_dict['batch_size']['min'] == 1
        assert schema_dict['batch_size']['max'] == 512

    def test_generates_defaults(self):
        """Should generate value and placeholder from defaults."""
        syncer = HyperparametersSyncer()
        action_info = {'params_model': SimpleParams}
        action_config: dict = {}

        syncer.sync('train', action_info, action_config)

        schema = action_config['hyperparameters']['train_ui_schemas']
        schema_dict = {item['name']: item for item in schema}

        assert schema_dict['epochs']['value'] == 50
        assert schema_dict['epochs']['placeholder'] == 50

    def test_generates_help_from_description(self):
        """Should generate help text from field description."""
        syncer = HyperparametersSyncer()
        action_info = {'params_model': SimpleParams}
        action_config: dict = {}

        syncer.sync('train', action_info, action_config)

        schema = action_config['hyperparameters']['train_ui_schemas']
        schema_dict = {item['name']: item for item in schema}

        assert schema_dict['epochs']['help'] == 'Number of epochs'

    def test_applies_custom_formkit_type(self):
        """Should apply custom formkit type from json_schema_extra."""
        syncer = HyperparametersSyncer()
        action_info = {'params_model': ParamsWithCustomUI}
        action_config: dict = {}

        syncer.sync('train', action_info, action_config)

        schema = action_config['hyperparameters']['train_ui_schemas']
        schema_dict = {item['name']: item for item in schema}

        assert schema_dict['image_size']['$formkit'] == 'radio'
        assert schema_dict['image_size']['options'] == [320, 416, 512, 640]

    def test_applies_custom_step(self):
        """Should apply custom step from json_schema_extra."""
        syncer = HyperparametersSyncer()
        action_info = {'params_model': ParamsWithCustomUI}
        action_config: dict = {}

        syncer.sync('train', action_info, action_config)

        schema = action_config['hyperparameters']['train_ui_schemas']
        schema_dict = {item['name']: item for item in schema}

        assert schema_dict['momentum']['step'] == 0.01

    def test_no_change_when_schema_unchanged(self):
        """Should not report change when schema is identical."""
        syncer = HyperparametersSyncer()
        action_info = {'params_model': SimpleParams}

        # First sync
        action_config: dict = {}
        syncer.sync('train', action_info, action_config)

        # Second sync with same model
        changes = syncer.sync('train', action_info, action_config)

        assert changes == []


# =============================================================================
# sync_action_config Tests
# =============================================================================


class TestSyncActionConfig:
    """Tests for sync_action_config function."""

    def test_runs_all_default_syncers(self):
        """Should run all default syncers."""
        action_info = {
            'entrypoint': 'plugin.train.TrainAction',
            'input_type': 'yolo_dataset',
            'output_type': 'model_weights',
            'params_model': SimpleParams,
        }
        action_config: dict = {}

        changes = sync_action_config('train', action_info, action_config)

        assert 'entrypoint' in action_config
        assert 'input_type' in action_config
        assert 'output_type' in action_config
        assert 'hyperparameters' in action_config
        assert len(changes) == 5  # entrypoint, method, input_type, output_type, hyperparameters

    def test_uses_custom_syncers(self):
        """Should use custom syncers when provided."""
        action_info = {
            'entrypoint': 'plugin.train.TrainAction',
            'input_type': 'yolo_dataset',
        }
        action_config: dict = {}

        # Only use TypesSyncer
        changes = sync_action_config('train', action_info, action_config, syncers=[TypesSyncer()])

        assert 'entrypoint' not in action_config  # EntrypointSyncer not used
        assert 'input_type' in action_config
        assert len(changes) == 1

    def test_aggregates_changes_from_all_syncers(self):
        """Should aggregate changes from all syncers."""
        action_info = {
            'entrypoint': 'plugin.train.TrainAction',
            'input_type': 'yolo_dataset',
        }
        action_config: dict = {}

        changes = sync_action_config(
            'train',
            action_info,
            action_config,
            syncers=[EntrypointSyncer(), TypesSyncer()],
        )

        assert len(changes) == 2


# =============================================================================
# get_default_syncers Tests
# =============================================================================


class TestGetDefaultSyncers:
    """Tests for get_default_syncers function."""

    def test_returns_all_syncers(self):
        """Should return all default syncers."""
        syncers = get_default_syncers()

        assert len(syncers) == 4
        assert isinstance(syncers[0], EntrypointSyncer)
        assert isinstance(syncers[1], MethodSyncer)
        assert isinstance(syncers[2], TypesSyncer)
        assert isinstance(syncers[3], HyperparametersSyncer)

    def test_syncers_are_instances(self):
        """Should return syncer instances, not classes."""
        syncers = get_default_syncers()

        for syncer in syncers:
            assert isinstance(syncer, ConfigSyncer)

    def test_returns_new_instances(self):
        """Should return new instances on each call."""
        syncers1 = get_default_syncers()
        syncers2 = get_default_syncers()

        assert syncers1[0] is not syncers2[0]


# =============================================================================
# ConfigSyncer Base Class Tests
# =============================================================================


class TestConfigSyncerBase:
    """Tests for ConfigSyncer base class."""

    def test_syncer_has_name_property(self):
        """All syncers should have a name property."""
        for syncer in get_default_syncers():
            assert hasattr(syncer, 'name')
            assert isinstance(syncer.name, str)
            assert len(syncer.name) > 0

    def test_syncer_names_are_unique(self):
        """Syncer names should be unique."""
        syncers = get_default_syncers()
        names = [s.name for s in syncers]

        assert len(names) == len(set(names))
