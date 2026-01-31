"""Entrypoint module for running plugin actions via Ray Jobs API.

Usage: python -m synapse_sdk.plugins.entrypoint

This module is invoked by the RayJobsApiExecutor to run plugin actions.
It reads configuration from environment variables and dispatches the action.
"""

import importlib
import json
import logging
import os
import sys


def main() -> dict:
    """Run a plugin action based on environment configuration.

    Environment Variables:
        SYNAPSE_ACTION_ENTRYPOINT: Module path to action class (e.g., 'mymodule.MyAction')
        SYNAPSE_ACTION_PARAMS: JSON string of action parameters
        SYNAPSE_ACTION_PARAMS_FILE: Alternative: path to JSON file with parameters
        SYNAPSE_JOB_ID: Optional job ID (falls back to RAY_JOB_ID)

    Returns:
        Action result dict.

    Raises:
        ValueError: If required environment variables are missing.
    """
    # Configure logging to ensure ConsoleLogger output is visible
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        force=True,
    )

    # Add working directory to path
    cwd = os.getcwd()
    if cwd not in sys.path:
        sys.path.insert(0, cwd)

    # Load params from environment or file
    params_json = os.environ.get('SYNAPSE_ACTION_PARAMS')
    if not params_json:
        params_file = os.environ.get('SYNAPSE_ACTION_PARAMS_FILE')
        if params_file and os.path.exists(params_file):
            with open(params_file) as f:
                params_json = f.read()

    if not params_json:
        raise ValueError('No params provided via SYNAPSE_ACTION_PARAMS or SYNAPSE_ACTION_PARAMS_FILE')

    params = json.loads(params_json)

    # Get entrypoint
    entrypoint = os.environ.get('SYNAPSE_ACTION_ENTRYPOINT')
    if not entrypoint:
        raise ValueError('SYNAPSE_ACTION_ENTRYPOINT not set')

    # Import action class
    module_path, class_name = entrypoint.rsplit('.', 1)
    module = importlib.import_module(module_path)
    action_cls = getattr(module, class_name)

    # Create context
    from synapse_sdk.loggers import ConsoleLogger
    from synapse_sdk.plugins.context import RuntimeContext
    from synapse_sdk.plugins.context.env import PluginEnvironment
    from synapse_sdk.utils.auth import create_backend_client

    client = create_backend_client()
    # Use SYNAPSE_JOB_ID (explicitly passed) with fallback to RAY_JOB_ID
    job_id = os.environ.get('SYNAPSE_JOB_ID') or os.environ.get('RAY_JOB_ID')

    if client and job_id:
        from synapse_sdk.loggers import JobLogger

        logger = JobLogger(client=client, job_id=job_id)
        print(f'INFO: Using JobLogger with job_id={job_id}', flush=True)
    else:
        logger = ConsoleLogger()
        print(f'INFO: Using ConsoleLogger (client={"set" if client else "None"}, job_id={job_id})', flush=True)
    ctx = RuntimeContext(
        logger=logger,
        env=PluginEnvironment.from_environ(),
        job_id=job_id,
        client=client,
    )

    # Dispatch action (handles serve deployments, param validation, etc.)
    result = action_cls.dispatch(params, ctx)

    logger.finish()

    # Output result as JSON for capture
    print('__SYNAPSE_RESULT_START__')
    print(json.dumps(result if isinstance(result, dict) else {'result': result}))
    print('__SYNAPSE_RESULT_END__')

    return result


if __name__ == '__main__':
    main()
