"""Test generation module for Meraki API GET endpoints."""

import logging
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

import jinja2
from openapi_pydantic.v3.v3_0 import OpenAPI, Operation, Parameter, ParameterLocation, Reference

from codegen.constants import TEMPLATE_DIR
from codegen.utils import to_snake_case

log = logging.getLogger("codegen")

TEST_OUTPUT_DIR = "tests/generated"

# Path parameters we have fixtures for (in original camelCase from OpenAPI spec)
ALLOWED_PATH_PARAMS = {"organizationId", "networkId", "serial"}

# Regex to extract path parameters from a path like /organizations/{organizationId}/networks
PATH_PARAM_RE = re.compile(r"\{(\w+)\}")


@dataclass
class EndpointInfo:
    """Information about a testable endpoint."""

    operation_id: str
    function_name: str
    scope: str
    path_params: list[str]
    is_paginated: bool


@dataclass
class _Templates:
    """Jinja templates for test generation."""

    conftest_template: jinja2.Template
    test_module_template: jinja2.Template


def generate_tests(spec: OpenAPI, *, skip_tests: set[str] | None = None) -> None:
    """Generate test files for GET endpoints.

    Args:
        spec: The parsed OpenAPI specification.
        skip_tests: Set of operation IDs to skip in test generation.

    Raises:
        ValueError: If skip_tests contains operation IDs not found in the spec.

    """
    skip_tests = skip_tests or set()
    if skip_tests:
        _validate_skip_tests(spec, skip_tests)

    templates = _init_test_templates()
    endpoints_by_scope = _filter_testable_endpoints(spec, skip_tests=skip_tests)

    if not endpoints_by_scope:
        log.warning("No testable endpoints found")
        return

    _recreate_test_directories()

    # Generate conftest.py
    conftest_path = Path(TEST_OUTPUT_DIR) / "conftest.py"
    conftest_path.write_text(templates.conftest_template.render())

    # Generate __init__.py for api folder
    api_init_path = Path(TEST_OUTPUT_DIR) / "api" / "__init__.py"
    api_init_path.write_text('"""API integration tests."""\n')

    # Generate test module for each scope
    test_count = 0
    for scope, endpoints in sorted(endpoints_by_scope.items()):
        module_name = to_snake_case(scope)
        test_file_path = Path(TEST_OUTPUT_DIR) / "api" / f"test_{module_name}.py"

        content = templates.test_module_template.render(
            scope=scope,
            module_name=module_name,
            endpoints=endpoints,
        )
        test_file_path.write_text(content)
        test_count += len(endpoints)

    _format_test_code(TEST_OUTPUT_DIR)
    log.info(
        f"Generated {test_count} tests across {len(endpoints_by_scope)} modules in {TEST_OUTPUT_DIR}/"
    )


def _validate_skip_tests(spec: OpenAPI, skip_tests: set[str]) -> None:
    """Validate that all skip_tests operation IDs exist in the spec."""
    spec_operation_ids = {
        path_item.get.operationId
        for path_item in spec.paths.values()
        if path_item.get and path_item.get.operationId
    }
    unknown = skip_tests - spec_operation_ids
    if unknown:
        raise ValueError(f"skip_tests contains unknown operation IDs: {sorted(unknown)}")


def _filter_testable_endpoints(
    spec: OpenAPI, *, skip_tests: set[str]
) -> dict[str, list[EndpointInfo]]:
    """Filter GET endpoints that only use allowed path parameters and have no required query params.

    Returns:
        Dictionary mapping scope name to list of EndpointInfo.

    """
    endpoints_by_scope: dict[str, list[EndpointInfo]] = {}

    for path, path_item in spec.paths.items():
        operation = path_item.get
        if not operation:
            continue

        # Extract path parameters from the URL
        path_params = PATH_PARAM_RE.findall(path)

        # Check if all path params are in our allowed set
        if not all(param in ALLOWED_PATH_PARAMS for param in path_params):
            continue

        operation_id = operation.operationId
        if not operation_id:
            continue

        # Skip tests explicitly excluded in spec_overrides
        if operation_id in skip_tests:
            continue

        # Check for required query parameters - skip if any exist
        if _has_required_query_params(operation):
            continue

        # Get scope from first tag
        scope = operation.tags[0] if operation.tags else None
        if not scope:
            continue

        # Determine if endpoint is paginated
        is_paginated = _is_paginated(operation)

        # Convert path params to snake_case for function arguments
        snake_path_params = [to_snake_case(p) for p in path_params]

        endpoint = EndpointInfo(
            operation_id=operation_id,
            function_name=to_snake_case(operation_id),
            scope=scope,
            path_params=snake_path_params,
            is_paginated=is_paginated,
        )

        endpoints_by_scope.setdefault(scope, []).append(endpoint)

    return endpoints_by_scope


def _has_required_query_params(operation: Operation) -> bool:
    """Check if operation has required query parameters (non-path params)."""
    if not operation.parameters:
        return False

    for param in operation.parameters:
        if isinstance(param, Reference):
            continue
        if isinstance(param, Parameter):
            # Skip path parameters - we handle those separately
            if param.param_in == ParameterLocation.PATH:
                continue
            # Check if this is a required query/header parameter
            if param.required:
                return True

    return False


def _is_paginated(operation: Operation) -> bool:
    """Check if an operation is paginated by looking for per_page parameter."""
    if not operation.parameters:
        return False

    for param in operation.parameters:
        if isinstance(param, Reference):
            continue
        if isinstance(param, Parameter) and param.name == "perPage":
            return True

    return False


def _recreate_test_directories() -> None:
    """Recreate generated test directories."""
    generated_dir = Path(TEST_OUTPUT_DIR)

    # Remove existing generated directory if it exists
    if generated_dir.exists():
        shutil.rmtree(generated_dir)

    # Create directories
    api_dir = generated_dir / "api"
    api_dir.mkdir(parents=True, exist_ok=True)

    # Create __init__.py for generated folder
    (generated_dir / "__init__.py").write_text('"""Generated API integration tests."""\n')


def _init_test_templates() -> _Templates:
    """Initialize Jinja templates for test generation."""
    jinja_env = jinja2.Environment(  # noqa: S701
        trim_blocks=True, lstrip_blocks=True, keep_trailing_newline=True
    )
    return _Templates(
        conftest_template=_read_template("test_conftest_template.py", jinja_env),
        test_module_template=_read_template("test_module_template.py", jinja_env),
    )


def _read_template(template_name: str, jinja_env: jinja2.Environment) -> jinja2.Template:
    """Read a template from the template directory."""
    with open(
        os.path.join(TEMPLATE_DIR, f"{template_name}.jinja2"), encoding="utf-8", newline=None
    ) as fp:
        return jinja_env.from_string(fp.read())


def _format_test_code(output_dir: str) -> None:
    """Format generated test code using ruff."""
    subprocess.run(  # noqa: S603
        ["uv", "run", "ruff", "check", "--quiet", "--select", "I,F401", "--fix", output_dir],  # noqa: S607
        check=True,
    )
    subprocess.run(  # noqa: S603
        ["uv", "run", "ruff", "format", "--quiet", output_dir],  # noqa: S607
        check=True,
    )
