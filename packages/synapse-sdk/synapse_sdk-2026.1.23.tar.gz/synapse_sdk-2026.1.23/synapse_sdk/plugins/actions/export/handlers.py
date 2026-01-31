"""Export target handlers for different data sources.

This module provides handlers for exporting data from different target sources:
    - AssignmentExportTargetHandler: Export from assignments
    - GroundTruthExportTargetHandler: Export from ground truth datasets
    - TaskExportTargetHandler: Export from tasks
    - TargetHandlerFactory: Factory for creating appropriate handlers

Example:
    >>> handler = TargetHandlerFactory.get_handler('assignment')
    >>> handler.validate_filter({'project': 123}, client)
    >>> results, count = handler.get_results(client, {'project': 123})
    >>> for item in handler.get_export_item(results):
    ...     process(item)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Generator

from pydantic_core import PydanticCustomError

from synapse_sdk.clients.exceptions import ClientError

if TYPE_CHECKING:
    from synapse_sdk.clients.backend import BackendClient


class ExportTargetHandler(ABC):
    """Abstract base class for handling export targets.

    This class defines the blueprint for export target handlers, requiring the implementation
    of methods to validate filters, retrieve results, and process collections of results.
    """

    @abstractmethod
    def validate_filter(self, value: dict[str, Any], client: BackendClient) -> dict[str, Any]:
        """Validate filter query params to request original data from api.

        Args:
            value: The filter criteria to validate.
            client: The client used to validate the filter.

        Returns:
            The validated filter criteria.

        Raises:
            PydanticCustomError: If the filter criteria are invalid.
        """
        pass

    @abstractmethod
    def get_results(self, client: BackendClient, filters: dict[str, Any]) -> tuple[Any, int]:
        """Retrieve original data from target sources.

        Args:
            client: The client used to retrieve the results.
            filters: The filter criteria to apply.

        Returns:
            A tuple containing the results and the total count of results.
        """
        pass

    @abstractmethod
    def get_export_item(self, results: Any) -> Generator[dict[str, Any], None, None]:
        """Providing elements to build export data.

        Args:
            results: The results to process.

        Yields:
            A generator that yields processed data items.
        """
        pass


class AssignmentExportTargetHandler(ExportTargetHandler):
    """Handler for assignment target exports.

    Implements ExportTargetHandler interface for assignment-specific
    export operations including validation, data retrieval, and processing.
    """

    def validate_filter(self, value: dict[str, Any], client: BackendClient) -> dict[str, Any]:
        """Validate assignment filter criteria.

        Args:
            value: Filter criteria containing 'project' key.
            client: Backend client for validation.

        Returns:
            Validated filter criteria.

        Raises:
            PydanticCustomError: If 'project' is missing or client request fails.
        """
        if 'project' not in value:
            raise PydanticCustomError('missing_field', 'Project is required for Assignment.')
        try:
            client.list_assignments(params=value)
        except ClientError:
            raise PydanticCustomError('client_error', 'Unable to get Assignment.')
        return value

    def get_results(self, client: BackendClient, filters: dict[str, Any]) -> tuple[Any, int]:
        """Retrieve assignments from the API.

        Args:
            client: Backend client for data retrieval.
            filters: Filter criteria for assignments.

        Returns:
            Tuple of (results, count).
        """
        return client.list_assignments(params=filters, list_all=True)

    def get_export_item(self, results: Any) -> Generator[dict[str, Any], None, None]:
        """Process assignment results into export items.

        Args:
            results: Assignment results from the API.

        Yields:
            Export item dicts with 'data', 'files', and 'id' keys.
        """
        for result in results:
            yield {
                'data': result['data'],
                'files': result['file'],
                'id': result['id'],
            }


class GroundTruthExportTargetHandler(ExportTargetHandler):
    """Handler for ground truth target exports.

    Implements ExportTargetHandler interface for ground truth dataset
    export operations including validation, data retrieval, and processing.
    """

    def validate_filter(self, value: dict[str, Any], client: BackendClient) -> dict[str, Any]:
        """Validate ground truth filter criteria.

        Args:
            value: Filter criteria containing 'ground_truth_dataset_version' key.
            client: Backend client for validation.

        Returns:
            Validated filter criteria.

        Raises:
            PydanticCustomError: If 'ground_truth_dataset_version' is missing or client request fails.
        """
        if 'ground_truth_dataset_version' not in value:
            raise PydanticCustomError('missing_field', 'Ground Truth dataset version is required.')
        try:
            client.get_ground_truth_version(value['ground_truth_dataset_version'])
        except ClientError:
            raise PydanticCustomError('client_error', 'Unable to get Ground Truth dataset version.')
        return value

    def get_results(self, client: BackendClient, filters: dict[str, Any]) -> tuple[Any, int]:
        """Retrieve ground truth events from the API.

        Args:
            client: Backend client for data retrieval.
            filters: Filter criteria for ground truth events.

        Returns:
            Tuple of (results, count).
        """
        filters['ground_truth_dataset_versions'] = filters.pop('ground_truth_dataset_version')
        return client.list_ground_truth_events(params=filters, list_all=True)

    def get_export_item(self, results: Any) -> Generator[dict[str, Any], None, None]:
        """Process ground truth results into export items.

        Args:
            results: Ground truth results from the API.

        Yields:
            Export item dicts with 'data', 'files', and 'id' keys.
        """
        for result in results:
            files_key = next(iter(result['data_unit']['files']))
            yield {
                'data': result['data'],
                'files': result['data_unit']['files'][files_key],
                'id': result['id'],
            }


class TaskExportTargetHandler(ExportTargetHandler):
    """Handler for task target exports.

    Implements ExportTargetHandler interface for task-specific
    export operations including validation, data retrieval, and processing.
    """

    def validate_filter(self, value: dict[str, Any], client: BackendClient) -> dict[str, Any]:
        """Validate task filter criteria.

        Args:
            value: Filter criteria containing 'project' key.
            client: Backend client for validation.

        Returns:
            Validated filter criteria.

        Raises:
            PydanticCustomError: If 'project' is missing or client request fails.
        """
        if 'project' not in value:
            raise PydanticCustomError('missing_field', 'Project is required for Task.')
        try:
            client.list_tasks(params=value)
        except ClientError:
            raise PydanticCustomError('client_error', 'Unable to get Task.')
        return value

    def get_results(self, client: BackendClient, filters: dict[str, Any]) -> tuple[Any, int]:
        """Retrieve tasks from the API.

        Args:
            client: Backend client for data retrieval.
            filters: Filter criteria for tasks.

        Returns:
            Tuple of (results, count).
        """
        filters['expand'] = ['data_unit', 'assignment', 'workshop']
        return client.list_tasks(params=filters, list_all=True)

    def get_export_item(self, results: Any) -> Generator[dict[str, Any], None, None]:
        """Process task results into export items.

        Args:
            results: Task results from the API.

        Yields:
            Export item dicts with 'data', 'files', and 'id' keys.
        """
        for result in results:
            files_key = next(iter(result['data_unit']['files']))
            yield {
                'data': result['data'],
                'files': result['data_unit']['files'][files_key],
                'id': result['id'],
            }


class TargetHandlerFactory:
    """Factory class for creating export target handlers.

    Provides a centralized way to create appropriate target handlers
    based on the target type. Supports assignment, ground_truth, and task targets.

    Example:
        >>> handler = TargetHandlerFactory.get_handler('assignment')
        >>> isinstance(handler, AssignmentExportTargetHandler)
        True
    """

    _handlers: dict[str, type[ExportTargetHandler]] = {
        'assignment': AssignmentExportTargetHandler,
        'ground_truth': GroundTruthExportTargetHandler,
        'task': TaskExportTargetHandler,
    }

    @classmethod
    def get_handler(cls, target: str) -> ExportTargetHandler:
        """Get the appropriate target handler for the given target type.

        Args:
            target: The target type ('assignment', 'ground_truth', 'task')

        Returns:
            The appropriate handler instance.

        Raises:
            ValueError: If the target type is not supported.

        Example:
            >>> handler = TargetHandlerFactory.get_handler('assignment')
            >>> handler.validate_filter({'project': 123}, client)
        """
        handler_class = cls._handlers.get(target)
        if handler_class is None:
            supported = ', '.join(cls._handlers.keys())
            raise ValueError(f"Unknown target: '{target}'. Supported targets: {supported}")
        return handler_class()

    @classmethod
    def register_handler(cls, target: str, handler_class: type[ExportTargetHandler]) -> None:
        """Register a custom target handler.

        Args:
            target: The target type name.
            handler_class: The handler class to register.

        Example:
            >>> class CustomHandler(ExportTargetHandler):
            ...     # implementation
            >>> TargetHandlerFactory.register_handler('custom', CustomHandler)
        """
        cls._handlers[target] = handler_class
