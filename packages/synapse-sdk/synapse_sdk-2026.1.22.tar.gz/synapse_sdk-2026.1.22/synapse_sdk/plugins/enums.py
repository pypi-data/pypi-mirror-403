from __future__ import annotations

from enum import StrEnum


class PluginCategory(StrEnum):
    """Categories for organizing plugins by functionality."""

    NEURAL_NET = 'neural_net'
    EXPORT = 'export'
    UPLOAD = 'upload'
    SMART_TOOL = 'smart_tool'
    POST_ANNOTATION = 'post_annotation'
    PRE_ANNOTATION = 'pre_annotation'
    DATA_VALIDATION = 'data_validation'
    CUSTOM = 'custom'


class RunMethod(StrEnum):
    """Execution methods for plugin actions."""

    JOB = 'job'
    TASK = 'task'
    SERVE = 'serve'
    RESTAPI = 'restapi'


# Default execution method for well-known action names.
# Actions not listed here default to RunMethod.TASK.
ACTION_DEFAULT_METHODS: dict[str, RunMethod] = {
    'upload': RunMethod.JOB,
    'export': RunMethod.JOB,
    'download': RunMethod.JOB,
    'convert': RunMethod.JOB,
    'train': RunMethod.JOB,
    'test': RunMethod.JOB,
    'deployment': RunMethod.JOB,
    'inference': RunMethod.SERVE,
    'add_task_data': RunMethod.JOB,
    'auto_label': RunMethod.TASK,
}


class ExecutionMode(StrEnum):
    """Execution modes for run_plugin().

    Determines how the plugin action is executed:
    - LOCAL: In-process execution (sync, good for dev/testing)
    - TASK: Via Ray Actor pool (fast startup, <1s)
    - JOB: Via Ray Job API (for heavy/long-running workloads)
    """

    LOCAL = 'local'
    TASK = 'task'
    JOB = 'job'


class PackageManager(StrEnum):
    """Package managers for plugin dependencies."""

    PIP = 'pip'
    UV = 'uv'


class DataType(StrEnum):
    """Data types handled by plugins."""

    IMAGE = 'image'
    TEXT = 'text'
    VIDEO = 'video'
    PCD = 'pcd'
    AUDIO = 'audio'


class AnnotationCategory(StrEnum):
    """Annotation categories for smart tools."""

    OBJECT_DETECTION = 'object_detection'
    CLASSIFICATION = 'classification'
    SEGMENTATION = 'segmentation'
    KEYPOINT = 'keypoint'
    TEXT = 'text'


class AnnotationType(StrEnum):
    """Annotation types for smart tools."""

    BBOX = 'bbox'
    POLYGON = 'polygon'
    POINT = 'point'
    LINE = 'line'
    MASK = 'mask'
    LABEL = 'label'


class SmartToolType(StrEnum):
    """Smart tool implementation types."""

    INTERACTIVE = 'interactive'
    AUTOMATIC = 'automatic'
    SEMI_AUTOMATIC = 'semi_automatic'


__all__ = [
    'PluginCategory',
    'RunMethod',
    'ACTION_DEFAULT_METHODS',
    'ExecutionMode',
    'PackageManager',
    'DataType',
    'AnnotationCategory',
    'AnnotationType',
    'SmartToolType',
]
