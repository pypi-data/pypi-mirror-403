"""Auto-label action for smart tool plugins.

Provides BaseAutoLabelAction for implementing smart tool auto-labeling
with handle_input/handle_output pattern.
"""

from synapse_sdk.plugins.actions.auto_label.action import (
    AutoLabelParams,
    AutoLabelProgressCategories,
    AutoLabelResult,
    BaseAutoLabelAction,
)

__all__ = [
    'BaseAutoLabelAction',
    'AutoLabelParams',
    'AutoLabelProgressCategories',
    'AutoLabelResult',
]
