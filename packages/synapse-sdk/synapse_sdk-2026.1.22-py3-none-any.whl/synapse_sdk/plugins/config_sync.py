"""Modular config synchronization system.

This module provides a pluggable architecture for syncing different aspects
of plugin configuration from code to config.yaml.

Usage:
    from synapse_sdk.plugins.config_sync import get_default_syncers, sync_action_config

    syncers = get_default_syncers()
    changes = sync_action_config(action_name, action_info, action_config, syncers)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pydantic import BaseModel


class ConfigSyncer(ABC):
    """Base class for config syncers.

    Each syncer is responsible for syncing one aspect of action configuration
    from discovered code metadata to config.yaml.

    Subclass this to add new sync capabilities. Syncers are run in order,
    so later syncers can depend on changes made by earlier ones.

    Example:
        >>> class MySyncer(ConfigSyncer):
        ...     name = 'my_feature'
        ...
        ...     def sync(self, action_name, action_info, action_config):
        ...         if 'my_field' not in action_config:
        ...             action_config['my_field'] = 'default'
        ...             return ['my_field=default']
        ...         return []
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of this syncer for logging."""
        ...

    @abstractmethod
    def sync(
        self,
        action_name: str,
        action_info: dict[str, Any],
        action_config: dict[str, Any],
    ) -> list[str]:
        """Sync config for an action.

        Mutates action_config in place to apply any necessary changes.

        Args:
            action_name: Name of the action being synced
            action_info: Discovered metadata from code (entrypoint, types, params_model, etc.)
            action_config: Mutable dict of current action config (will be modified)

        Returns:
            List of change descriptions for logging (e.g., ['input_type=yolo_dataset'])
        """
        ...


class EntrypointSyncer(ConfigSyncer):
    """Syncs action entrypoints from discovered code."""

    name = 'entrypoint'

    def sync(
        self,
        action_name: str,
        action_info: dict[str, Any],
        action_config: dict[str, Any],
    ) -> list[str]:
        entrypoint = action_info.get('entrypoint')
        if not entrypoint:
            return []

        if action_config.get('entrypoint') != entrypoint:
            action_config['entrypoint'] = entrypoint
            return [f'entrypoint={entrypoint}']
        return []


class TypesSyncer(ConfigSyncer):
    """Syncs input_type and output_type from discovered code."""

    name = 'types'

    def sync(
        self,
        action_name: str,
        action_info: dict[str, Any],
        action_config: dict[str, Any],
    ) -> list[str]:
        changes = []

        input_type = action_info.get('input_type')
        if input_type and action_config.get('input_type') != input_type:
            action_config['input_type'] = input_type
            changes.append(f'input_type={input_type}')

        output_type = action_info.get('output_type')
        if output_type and action_config.get('output_type') != output_type:
            action_config['output_type'] = output_type
            changes.append(f'output_type={output_type}')

        return changes


class MethodSyncer(ConfigSyncer):
    """Syncs action method from discovered code or category defaults.

    Sets the execution method for actions. If the action class defines a
    ``method`` attribute, that value is used. Otherwise, well-known actions
    have predefined defaults from ``ACTION_DEFAULT_METHODS`` in enums.py
    (e.g. train → job, inference → serve).

    Actions not listed in the defaults keep whatever is already in config.yaml.
    """

    name = 'method'

    def sync(
        self,
        action_name: str,
        action_info: dict[str, Any],
        action_config: dict[str, Any],
    ) -> list[str]:
        from synapse_sdk.plugins.enums import ACTION_DEFAULT_METHODS

        # Determine the expected method
        discovered_method = action_info.get('method')
        if discovered_method:
            expected = str(discovered_method)
        elif action_name in ACTION_DEFAULT_METHODS:
            expected = str(ACTION_DEFAULT_METHODS[action_name])
        else:
            return []

        current = action_config.get('method')
        if current == expected:
            return []

        action_config['method'] = expected
        return [f'method={expected}']


class HyperparametersSyncer(ConfigSyncer):
    """Syncs hyperparameters FormKit schema from Pydantic params model.

    Generates a FormKit-compatible UI schema from the action's params_model.
    The schema location depends on the action type:
    - train/tune: writes to hyperparameters.train_ui_schemas
    - upload: writes to ui_schema (at action level)

    Only applies to specific action types (train, tune, upload).

    All fields are included by default. To exclude a field, use json_schema_extra:
        - exclude_from_ui=True: Exclude from UI schema

    Common internal fields (data_path, checkpoint, etc.) are excluded automatically
    via DEFAULT_EXCLUDED_FIELDS.

    Example:
        >>> class TrainParams(BaseModel):
        ...     # Included in UI (default behavior)
        ...     epochs: int = Field(default=100)
        ...     batch_size: int = Field(default=16)
        ...
        ...     # Excluded - not user-configurable
        ...     internal_flag: bool = Field(False, json_schema_extra={'exclude_from_ui': True})
    """

    name = 'hyperparameters'

    # Action types that should have hyperparameters generated
    SUPPORTED_ACTIONS = frozenset({'train', 'tune', 'upload'})

    # Fields to exclude by default (common internal/pipeline fields)
    DEFAULT_EXCLUDED_FIELDS = frozenset({
        'data_path',
        'dataset_path',
        'dataset',
        'splits',
        'checkpoint',
        'model_path',
        'weights_path',
        'output_path',
        'work_dir',
        'is_tune',
        'hyperparameters',
    })

    def sync(
        self,
        action_name: str,
        action_info: dict[str, Any],
        action_config: dict[str, Any],
    ) -> list[str]:
        # Only generate hyperparameters for supported action types
        if action_name not in self.SUPPORTED_ACTIONS:
            return []

        params_model = action_info.get('params_model')
        if params_model is None:
            return []

        # Generate schema, filtering out excluded fields
        # For train/tune actions, all params are required by default
        force_required = action_name in ('train', 'tune')
        schema = self._generate_schema(params_model, force_required=force_required)
        if not schema:
            return []

        # Determine schema location based on action type
        # upload actions use ui_schema at action level
        # train/tune actions use hyperparameters.train_ui_schemas
        if action_name == 'upload':
            current_schema = action_config.get('ui_schema', [])
            schema_key = 'ui_schema'
        else:
            current_hyperparams = action_config.get('hyperparameters', {})
            current_schema = current_hyperparams.get('train_ui_schemas', [])
            schema_key = 'hyperparameters.train_ui_schemas'

        # Compare schemas (simple comparison by field names and types)
        if self._schemas_equal(schema, current_schema):
            return []

        # Update config based on action type
        if action_name == 'upload':
            action_config['ui_schema'] = schema
        else:
            if 'hyperparameters' not in action_config:
                action_config['hyperparameters'] = {}
            action_config['hyperparameters']['train_ui_schemas'] = schema

        field_names = [item['name'] for item in schema]
        return [f'{schema_key}=[{", ".join(field_names)}]']

    def _generate_schema(self, model: type[BaseModel], *, force_required: bool = False) -> list[dict[str, Any]]:
        """Generate FormKit schema from Pydantic model, excluding internal fields.

        Args:
            model: Pydantic model class
            force_required: If True, all fields are marked as required (for train/tune)

        Exclusion can be set at two levels:
            - Model level: model_config = {'json_schema_extra': {'exclude_from_ui': True}}
            - Field level: Field(json_schema_extra={'exclude_from_ui': True})
        """
        from synapse_sdk.plugins.utils import pydantic_to_ui_schema

        # Check model-level exclusion via model_config.json_schema_extra
        model_extra = getattr(model, 'model_config', {}).get('json_schema_extra')
        if isinstance(model_extra, dict) and model_extra.get('exclude_from_ui'):
            return []

        # Get full schema
        full_schema = pydantic_to_ui_schema(model)

        # Filter fields - include all by default, opt-out via exclude_from_ui
        filtered_schema = []
        for item in full_schema:
            field_name = item['name']

            # Check if field is excluded by default (common internal fields)
            if field_name in self.DEFAULT_EXCLUDED_FIELDS:
                continue

            field_info = model.model_fields.get(field_name)
            if not field_info:
                continue

            # Check for explicit exclusion via json_schema_extra
            extra = field_info.json_schema_extra
            if extra:
                if callable(extra):
                    extra_dict: dict[str, Any] = {}
                    extra(extra_dict)
                    extra = extra_dict

                if isinstance(extra, dict) and extra.get('exclude_from_ui'):
                    continue

            # For train/tune actions, all params are required by default
            if force_required and 'required' not in item:
                item['required'] = True

            filtered_schema.append(item)

        return filtered_schema

    def _schemas_equal(self, schema1: list[dict[str, Any]], schema2: list[dict[str, Any]]) -> bool:
        """Check if two FormKit schemas are equivalent."""
        if len(schema1) != len(schema2):
            return False

        # Compare by serialized form for simplicity
        # This handles nested structures correctly
        import json

        try:
            return json.dumps(schema1, sort_keys=True) == json.dumps(schema2, sort_keys=True)
        except (TypeError, ValueError):
            return False


def get_default_syncers() -> list[ConfigSyncer]:
    """Get the default list of config syncers.

    Returns syncers in the order they should be applied:
    1. EntrypointSyncer - ensures entrypoint is set
    2. TypesSyncer - syncs input/output types
    3. HyperparametersSyncer - syncs FormKit schema from params model

    Returns:
        List of ConfigSyncer instances
    """
    return [
        EntrypointSyncer(),
        MethodSyncer(),
        TypesSyncer(),
        HyperparametersSyncer(),
    ]


def sync_action_config(
    action_name: str,
    action_info: dict[str, Any],
    action_config: dict[str, Any],
    syncers: list[ConfigSyncer] | None = None,
) -> list[str]:
    """Run all syncers on an action's config.

    Args:
        action_name: Name of the action
        action_info: Discovered metadata from code
        action_config: Mutable dict of action config (will be modified)
        syncers: List of syncers to run (defaults to get_default_syncers())

    Returns:
        List of all change descriptions from all syncers
    """
    if syncers is None:
        syncers = get_default_syncers()

    all_changes: list[str] = []
    for syncer in syncers:
        changes = syncer.sync(action_name, action_info, action_config)
        all_changes.extend(changes)

    return all_changes
