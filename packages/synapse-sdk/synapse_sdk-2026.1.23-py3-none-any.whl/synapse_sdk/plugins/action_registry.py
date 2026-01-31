"""Action registry for plugin template discovery.

Provides centralized metadata for plugin actions, eliminating hard-coded
mappings in plugin creation. Auto-discovers actions from template directories.

Example:
    >>> from synapse_sdk.plugins.action_registry import get_action_registry
    >>> from synapse_sdk.plugins.enums import PluginCategory
    >>>
    >>> registry = get_action_registry()
    >>> spec = registry.get_primary_action(PluginCategory.UPLOAD)
    >>> spec.entrypoint_pattern
    'plugin.upload.UploadAction'
"""

from __future__ import annotations

import ast
import functools
import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, Iterator

if TYPE_CHECKING:
    from synapse_sdk.plugins.enums import PluginCategory


class ActionType(StrEnum):
    """Type of action entry (class-based or function-based)."""

    CLASS = 'class'
    FUNCTION = 'function'


@dataclass(frozen=True, slots=True)
class ActionSpec:
    """Specification for a plugin action.

    Immutable dataclass representing a single action's metadata,
    used for template generation and config.yaml creation.

    Attributes:
        name: Action identifier (e.g., 'train', 'upload', 'export').
        category: Plugin category this action belongs to.
        template_file: Template filename without extension (e.g., 'train').
        class_name: Name of the class or function in the template.
        action_type: Whether this is a class-based or function-based action.
        description: Human-readable description.
        is_primary: Whether this is the default/primary action for the category.

    Example:
        >>> from synapse_sdk.plugins.enums import PluginCategory
        >>> spec = ActionSpec(
        ...     name='train',
        ...     category=PluginCategory.NEURAL_NET,
        ...     template_file='train',
        ...     class_name='train',
        ...     action_type=ActionType.FUNCTION,
        ...     is_primary=True,
        ... )
        >>> spec.entrypoint_pattern
        'plugin.train.train'
    """

    name: str
    category: 'PluginCategory'
    template_file: str
    class_name: str
    action_type: ActionType
    description: str = ''
    is_primary: bool = False

    @property
    def template_path(self) -> str:
        """Relative template path: '{category}/plugin/{template_file}.py.j2'."""
        return f'{self.category.value}/plugin/{self.template_file}.py.j2'

    @property
    def entrypoint_pattern(self) -> str:
        """Entrypoint pattern: 'plugin.{name}.{class_name}'.

        This is the default entrypoint format used in config.yaml.
        """
        return f'plugin.{self.name}.{self.class_name}'

    @property
    def output_filename(self) -> str:
        """Output filename for generated code: '{template_file}.py'."""
        return f'{self.template_file}.py'


class ActionRegistry:
    """Registry for discovering and managing plugin actions.

    Auto-discovers actions from template directories and provides
    lookup methods for action metadata. Uses singleton pattern.

    This registry serves as the single source of truth for:
    - Available actions per category
    - Default action for each category
    - Action -> Class name mapping
    - Entrypoint generation

    Discovery Method:
        Scans templates/{category}/plugin/*.py.j2 files and parses them
        using AST to extract class/function names and action_name attributes.

    Example:
        >>> from synapse_sdk.plugins.enums import PluginCategory
        >>> registry = ActionRegistry()
        >>> registry.get_primary_action(PluginCategory.NEURAL_NET)
        ActionSpec(name='train', ...)

        >>> registry.get_action('upload', PluginCategory.UPLOAD)
        ActionSpec(name='upload', class_name='UploadAction', ...)

        >>> list(registry.list_actions(PluginCategory.PRE_ANNOTATION))
        [ActionSpec(name='pre_annotate', ...), ActionSpec(name='add_task_data', ...)]
    """

    _instance: ActionRegistry | None = None

    def __new__(cls) -> ActionRegistry:
        """Singleton pattern for global registry access."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        """Initialize the registry (only runs once due to singleton)."""
        if self._initialized:
            return

        from synapse_sdk.plugins.templates import TEMPLATES_DIR

        self._templates_dir = TEMPLATES_DIR
        self._specs: dict[PluginCategory, dict[str, ActionSpec]] = {}
        self._primary_actions: dict[PluginCategory, str] = {}
        self._initialized = True
        self._discover_all()

    def _discover_all(self) -> None:
        """Discover all actions from template directories."""
        from synapse_sdk.plugins.enums import PluginCategory

        for category in PluginCategory:
            self._specs[category] = {}
            category_dir = self._templates_dir / category.value / 'plugin'
            if not category_dir.exists():
                continue

            templates = sorted(category_dir.glob('*.py.j2'))
            for template_path in templates:
                spec = self._parse_template(template_path, category)
                if spec:
                    self._specs[category][spec.name] = spec
                    # Primary action: explicitly marked or first discovered
                    if spec.is_primary or category not in self._primary_actions:
                        self._primary_actions[category] = spec.name

    def _parse_template(
        self,
        template_path: Path,
        category: 'PluginCategory',
    ) -> ActionSpec | None:
        """Parse a template file to extract action metadata.

        Uses AST to find:
        1. Class definitions with optional action_name attribute
        2. Top-level function definitions

        Args:
            template_path: Path to .py.j2 template file.
            category: Category this template belongs to.

        Returns:
            ActionSpec if valid action found, None otherwise.
        """
        try:
            content = template_path.read_text()
            # Remove Jinja2 syntax for valid Python parsing
            cleaned = self._strip_jinja_syntax(content)
            tree = ast.parse(cleaned)
        except (SyntaxError, OSError):
            return None

        # 'train.py.j2' -> 'train'
        template_file = template_path.stem.removesuffix('.py')

        # Look for class definitions — prefer classes with explicit action_name
        first_class: tuple[str, str] | None = None  # (class_name, action_name)
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                class_name = node.name
                action_name = template_file  # Default: filename
                has_explicit_name = False

                # Check for action_name class attribute
                for item in node.body:
                    if isinstance(item, ast.Assign):
                        for target in item.targets:
                            if isinstance(target, ast.Name) and target.id == 'action_name':
                                if isinstance(item.value, ast.Constant):
                                    action_name = item.value.value
                                    has_explicit_name = True

                if has_explicit_name:
                    # Found a class with explicit action_name — use it
                    is_primary = self._is_primary_action(template_file, category)
                    return ActionSpec(
                        name=action_name,
                        category=category,
                        template_file=template_file,
                        class_name=class_name,
                        action_type=ActionType.CLASS,
                        is_primary=is_primary,
                    )

                if first_class is None:
                    first_class = (class_name, action_name)

        # Fallback: use first class found (no explicit action_name)
        if first_class:
            is_primary = self._is_primary_action(template_file, category)
            return ActionSpec(
                name=first_class[1],
                category=category,
                template_file=template_file,
                class_name=first_class[0],
                action_type=ActionType.CLASS,
                is_primary=is_primary,
            )

        # Look for top-level function definitions
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.FunctionDef):
                func_name = node.name
                action_name = template_file
                is_primary = self._is_primary_action(template_file, category)

                return ActionSpec(
                    name=action_name,
                    category=category,
                    template_file=template_file,
                    class_name=func_name,
                    action_type=ActionType.FUNCTION,
                    is_primary=is_primary,
                )

        return None

    @staticmethod
    def _strip_jinja_syntax(content: str) -> str:
        """Remove Jinja2 syntax for Python AST parsing.

        Replaces {{ var }} with 'PLACEHOLDER' and removes {% %} blocks.
        """
        # Replace {{ ... }} with a placeholder string
        content = re.sub(r'\{\{[^}]*\}\}', "'PLACEHOLDER'", content)
        # Remove {% ... %} blocks
        content = re.sub(r'\{%[^%]*%\}', '', content)
        return content

    @staticmethod
    def _is_primary_action(template_file: str, category: 'PluginCategory') -> bool:
        """Determine if an action is the primary/default for its category.

        Uses naming conventions to identify the default action.
        """
        from synapse_sdk.plugins.enums import PluginCategory

        primary_map = {
            PluginCategory.NEURAL_NET: 'train',
            PluginCategory.UPLOAD: 'upload',
            PluginCategory.EXPORT: 'export',
            PluginCategory.DATA_VALIDATION: 'validate',
            PluginCategory.PRE_ANNOTATION: 'pre_annotate',
            PluginCategory.POST_ANNOTATION: 'post_annotate',
            PluginCategory.SMART_TOOL: 'auto_label',
            PluginCategory.CUSTOM: 'main',
        }
        return primary_map.get(category) == template_file

    # --- Public API ---

    def get_action(
        self,
        name: str,
        category: 'PluginCategory',
    ) -> ActionSpec | None:
        """Get action spec by name and category.

        Args:
            name: Action name (e.g., 'train', 'upload').
            category: Plugin category.

        Returns:
            ActionSpec if found, None otherwise.
        """
        return self._specs.get(category, {}).get(name)

    def get_primary_action(self, category: 'PluginCategory') -> ActionSpec | None:
        """Get the default/primary action for a category.

        This is the action used when creating a new plugin.

        Args:
            category: Plugin category.

        Returns:
            Primary ActionSpec for the category, None if no actions.
        """
        primary_name = self._primary_actions.get(category)
        if primary_name:
            return self.get_action(primary_name, category)
        return None

    def list_actions(self, category: 'PluginCategory') -> Iterator[ActionSpec]:
        """List all actions for a category.

        Args:
            category: Plugin category.

        Yields:
            ActionSpec for each action in the category.
        """
        yield from self._specs.get(category, {}).values()

    def list_all_actions(self) -> Iterator[ActionSpec]:
        """List all registered actions across all categories.

        Yields:
            ActionSpec for each registered action.
        """
        for category_specs in self._specs.values():
            yield from category_specs.values()

    def get_entrypoint(self, category: 'PluginCategory') -> str:
        """Get default entrypoint for a category's primary action.

        Convenience method for template generation.

        Args:
            category: Plugin category.

        Returns:
            Entrypoint string (e.g., 'plugin.train.train').

        Raises:
            ValueError: If category has no registered actions.
        """
        spec = self.get_primary_action(category)
        if not spec:
            msg = f'No actions registered for category: {category}'
            raise ValueError(msg)
        return spec.entrypoint_pattern

    def get_class_name(self, category: 'PluginCategory') -> str:
        """Get default class/function name for a category's primary action.

        Args:
            category: Plugin category.

        Returns:
            Class or function name.

        Raises:
            ValueError: If category has no registered actions.
        """
        spec = self.get_primary_action(category)
        if not spec:
            msg = f'No actions registered for category: {category}'
            raise ValueError(msg)
        return spec.class_name

    def has_category(self, category: 'PluginCategory') -> bool:
        """Check if a category has any registered actions."""
        return bool(self._specs.get(category))

    def refresh(self) -> None:
        """Re-discover all actions (useful after adding new templates)."""
        self._specs.clear()
        self._primary_actions.clear()
        self._discover_all()


@functools.lru_cache(maxsize=1)
def get_action_registry() -> ActionRegistry:
    """Get the global ActionRegistry instance.

    Uses LRU cache to ensure singleton behavior.

    Returns:
        Global ActionRegistry instance.

    Example:
        >>> from synapse_sdk.plugins.action_registry import get_action_registry
        >>> from synapse_sdk.plugins.enums import PluginCategory
        >>> registry = get_action_registry()
        >>> spec = registry.get_primary_action(PluginCategory.UPLOAD)
    """
    return ActionRegistry()


__all__ = [
    'ActionRegistry',
    'ActionSpec',
    'ActionType',
    'get_action_registry',
]
