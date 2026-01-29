"""A script that generates the Meraki Python library using the public OpenAPI specification."""

import json
import logging
import os
import re
import shutil
import subprocess
import sys
import textwrap
import time
import tomllib
from collections.abc import KeysView
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, TextIO, TypeAlias, TypeVar, assert_never
from urllib.parse import unquote

import httpx
import jinja2
from openapi_pydantic.v3.v3_0 import (
    DataType,
    OpenAPI,
    Operation,
    Parameter,
    ParameterLocation,
    Reference,
    RequestBody,
    Schema,
)
from pydantic import BaseModel
from pydantic.alias_generators import to_snake

from codegen.constants import SCRIPT_DIR, TEMPLATE_DIR
from codegen.log_config import setup_logging
from codegen.schema_gen import (
    SchemaRegistry,
    generate_response_schemas,
    get_response_schema_name,
)
from codegen.schemas import BatchableAction
from codegen.test_gen import generate_tests
from codegen.utils import (
    capitalize_first,
    escape_reserved_name,
    load_spec_overrides,
    sanitize_text,
    to_snake_case,
)

setup_logging()
log = logging.getLogger("codegen")

PROJECT_ROOT = Path(SCRIPT_DIR).parent
OUTPUT_DIR = "meraki_client"

REVERSE_PAGINATION = ["getNetworkEvents", "getOrganizationConfigurationChanges"]
INDENT_WIDTH = 12
DOCSTRING_LINE_WIDTH = 100 - INDENT_WIDTH

DOCS_DIR = "docs/api_reference"
MODULE_DISPLAY_TITLES: dict[str, str] = {
    "campusGateway": "Campus Gateway",
    "cellularGateway": "Cellular Gateway",
    "nac": "NAC",
    "sm": "Systems Manager",
    "wirelessController": "Wireless Controller",
}


@dataclass
class BodyParam:
    """Body parameter info."""

    snake_name: str
    orig_name: str
    is_schema: bool = False
    is_list: bool = False
    is_dict: bool = False


@dataclass
class FunctionDefinition:
    """Function definition parameters."""

    body_params: list[BodyParam] = field(default_factory=list)
    assert_blocks: list[tuple[str, list[str]]] = field(default_factory=list)
    param_descriptions: list[str] = field(default_factory=list)
    required_args: list[str] = field(default_factory=list)
    optional_args: list[str] = field(default_factory=list)
    query_params: list[tuple[str, str]] = field(default_factory=list)
    path_params: list[str] = field(default_factory=list)
    request_body_schemas_used: list[str] = field(default_factory=list)


@dataclass
class ModuleInfo:
    """Module information for template generation."""

    snake_name: str
    class_name: str
    attr_name: str


@dataclass
class Templates:
    """Jinja templates."""

    api_reference_template: jinja2.Template
    batch_class_template: jinja2.Template
    batch_function_template: jinja2.Template
    batch_init_template: jinja2.Template
    class_template: jinja2.Template
    function_template: jinja2.Template
    init_template: jinja2.Template
    schema_base_template: jinja2.Template
    schema_init_template: jinja2.Template
    schema_module_template: jinja2.Template
    session_template: jinja2.Template


PathsType: TypeAlias = dict[str, dict[Literal["get", "put", "post", "delete"], Operation]]


def main() -> None:
    """Main function to generate the library."""
    t_start = time.perf_counter()

    api_version = get_api_version()
    if not api_version.startswith("v"):
        api_version = f"v{api_version}"

    client_version = get_client_version()
    log.info(f"Client version: {client_version}")
    log.info(f"API version: {api_version}")

    spec = get_openapi_specification(api_version)
    batchable_actions = [
        BatchableAction.model_validate(action) for action in spec["x-batchable-actions"]
    ]
    generate_library(OpenAPI.model_validate(spec), batchable_actions, client_version, api_version)
    elapsed = time.perf_counter() - t_start
    log.info(f"Completed code generation in {elapsed:.2f}s")


def get_api_version() -> str:
    """Read the API version from .api-version file."""
    api_version_path = PROJECT_ROOT / ".api-version"
    return api_version_path.read_text().strip()


def get_client_version() -> str:
    """Read the client version from pyproject.toml."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    with pyproject_path.open("rb") as f:
        pyproject = tomllib.load(f)
    return pyproject["project"]["version"]


def get_min_python_version() -> tuple[int, int]:
    """Read the minimum Python version from .python-version file."""
    python_version_path = PROJECT_ROOT / ".python-version"
    version_str = python_version_path.read_text().strip()
    parts = version_str.split(".")
    return (int(parts[0]), int(parts[1]))


def get_openapi_specification(api_version: str) -> dict[str, Any]:
    """Retrieve the OpenAPI specification from GitHub repository.

    Caches the specification locally to avoid unnecessary network requests.
    """
    spec_path = PROJECT_ROOT / ".cache" / f"spec-{api_version}.json"
    if spec_path.exists():
        log.info("Using cached OpenAPI specification")
        with spec_path.open("r") as f:
            return json.load(f)

    spec_path.parent.mkdir(parents=True, exist_ok=True)

    log.info("Downloading OpenAPI specification from GitHub repository")
    try:
        with httpx.stream(
            "GET",
            f"https://raw.githubusercontent.com/meraki/openapi/refs/tags/{api_version}/openapi/spec3.json",
        ) as response:
            response.raise_for_status()
            with spec_path.open("w") as f:
                for chunk in response.iter_bytes():
                    f.write(chunk.decode("utf-8"))
    except httpx.HTTPError as e:
        sys.exit(f"Error retrieving OpenAPI specification: {e}")

    return json.load(spec_path.open("r"))


def generate_library(  # noqa: PLR0915
    spec: OpenAPI, batchable_actions: list[BatchableAction], version_number: str, api_version: str
) -> None:
    """Generate the Meraki Python library using the public OpenAPI specification."""
    batchable_actions_map = {action.summary: action.operation for action in batchable_actions}
    spec_overrides = load_spec_overrides()

    recreate_output_directory()
    copy_static_files()

    templates = init_templates()
    min_python_version = get_min_python_version()

    t_start = time.perf_counter()
    schema_registry = generate_response_schemas(spec, templates, OUTPUT_DIR)
    elapsed = time.perf_counter() - t_start
    log.info(f"Generated {len(schema_registry.schema_names)} response schemas in {elapsed:.2f}s")

    t_start = time.perf_counter()
    scopes: dict[str, PathsType] = {}
    operation_count = 0
    for path, path_item in spec.paths.items():
        operations: dict[
            Literal["get", "put", "post", "delete", "patch", "options", "head", "trace"],
            Operation | None,
        ] = {
            "get": path_item.get,
            "put": path_item.put,
            "post": path_item.post,
            "delete": path_item.delete,
            "patch": path_item.patch,
            "options": path_item.options,
            "head": path_item.head,
            "trace": path_item.trace,
        }
        for method, operation in operations.items():
            if not operation:
                continue
            if method in ["options", "head", "trace", "patch"]:
                log.warning(f"Unsupported method: {method} for path: {path}")
                continue
            # First tag is the scope
            scope = operation.tags[0] if operation.tags else None
            if not scope:
                log.warning(f"Operation {operation.operationId} has no tags")
                continue
            scopes.setdefault(scope, {}).setdefault(path, {})[method] = operation
            operation_count += 1

    # Collect module info for __init__.py generation
    modules = sorted(
        [
            ModuleInfo(
                snake_name=to_snake_case(scope),
                class_name=capitalize_first(scope),
                attr_name=to_snake_case(scope),
            )
            for scope in scopes
        ],
        key=lambda m: m.snake_name,
    )

    with open(f"{OUTPUT_DIR}/__init__.py", "w") as f:
        f.write(
            templates.init_template.render(
                modules=modules,
                version=version_number,
                api_version=api_version,
                min_python_version=min_python_version,
                is_async=False,
            )
        )
    with open(f"{OUTPUT_DIR}/aio/__init__.py", "w") as f:
        f.write(
            templates.init_template.render(
                modules=modules,
                version=version_number,
                api_version=api_version,
                min_python_version=min_python_version,
                is_async=True,
            )
        )

    with open(f"{OUTPUT_DIR}/_session.py", "w") as f:
        f.write(templates.session_template.render(is_async=False))
    with open(f"{OUTPUT_DIR}/aio/_session.py", "w") as f:
        f.write(templates.session_template.render(is_async=True))

    def generate_scope(scope: str, paths: PathsType) -> ModuleInfo | None:
        """Generate a single scope's modules.

        Returns:
            ModuleInfo if scope has batch endpoints, None otherwise.

        """
        module_name = to_snake_case(scope)
        with (
            open(f"{OUTPUT_DIR}/_api/{module_name}.py", "w") as output,
            open(f"{OUTPUT_DIR}/aio/_api/{module_name}.py", "w") as async_output,
        ):
            batch_content = generate_module(
                scope=scope,
                paths=paths,
                spec=spec,
                batchable_actions_map=batchable_actions_map,
                output=output,
                async_output=async_output,
                templates=templates,
                schema_registry=schema_registry,
                force_paginated=spec_overrides.force_paginated,
            )

        if batch_content:
            with open(f"{OUTPUT_DIR}/_api/batch/{module_name}.py", "w") as batch_output:
                batch_output.write(batch_content)
            return ModuleInfo(
                snake_name=module_name,
                class_name=capitalize_first(scope),
                attr_name=module_name,
            )
        return None

    batch_modules: list[ModuleInfo] = []
    with ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(generate_scope, scope, paths): scope for scope, paths in scopes.items()
        }
        for future in as_completed(futures):
            scope = futures[future]
            try:
                batch_module = future.result()
                if batch_module:
                    batch_modules.append(batch_module)
            except Exception:
                log.exception(f"Failed to generate {scope}")
                raise
            log.debug(f"Generated {scope}")

    batch_modules.sort(key=lambda m: m.snake_name)
    with open(f"{OUTPUT_DIR}/_api/batch/__init__.py", "w") as f:
        f.write(templates.batch_init_template.render(modules=batch_modules))
    elapsed = time.perf_counter() - t_start
    log.info(f"Generated {len(scopes)} modules and {operation_count} operations in {elapsed:.2f}s")

    t_start = time.perf_counter()
    _format_generated_code(OUTPUT_DIR)
    elapsed = time.perf_counter() - t_start
    log.info(f"Formatted generated code in {elapsed:.2f}s")

    t_start = time.perf_counter()
    generate_tests(spec, skip_tests=spec_overrides.skip_tests)
    elapsed = time.perf_counter() - t_start
    log.info(f"Generated tests in {elapsed:.2f}s")

    t_start = time.perf_counter()
    generate_api_reference_docs(scopes.keys(), templates)
    elapsed = time.perf_counter() - t_start
    log.info(f"Generated API reference docs in {elapsed:.2f}s")


def generate_module(  # noqa: PLR0915
    *,
    scope: str,
    paths: PathsType,
    spec: OpenAPI,
    batchable_actions_map: dict[str, str],
    output: TextIO,
    async_output: TextIO,
    templates: Templates,
    schema_registry: SchemaRegistry,
    force_paginated: set[str],
) -> str | None:
    """Generate a module for a scope.

    Returns:
        Batch module content if scope has batch endpoints, None otherwise.

    """
    class_name = capitalize_first(scope)
    schemas_used: list[str] = []
    batch_content: list[str] = []
    batch_schemas_used: list[str] = []
    operation_request_schemas: dict[str, list[str]] = {}

    for methods in paths.values():
        for method, endpoint in methods.items():
            operation_id = endpoint.operationId
            if not operation_id:
                continue

            # Collect request body schemas for this operation
            op_schemas: list[str] = []
            for (op_id, _prop_name), param_schema in schema_registry.request_body_schemas.items():
                if op_id == operation_id:
                    if param_schema.item_class_name:
                        op_schemas.append(param_schema.item_class_name)
                    elif not param_schema.is_list:
                        op_schemas.append(param_schema.class_name)
            if op_schemas:
                operation_request_schemas[operation_id] = op_schemas
                schemas_used.extend(op_schemas)

            if method == "delete":
                continue

            response_schema_name = get_response_schema_name(operation_id)
            if response_schema_name in schema_registry.schema_names:
                schemas_used.append(response_schema_name)
                if response_schema_name in schema_registry.item_schema_map:
                    schemas_used.extend(schema_registry.item_schema_map[response_schema_name])

    output.write(
        templates.class_template.render(
            class_name=class_name, is_async=False, schemas_used=sorted(set(schemas_used))
        )
    )
    async_output.write(
        templates.class_template.render(
            class_name=class_name, is_async=True, schemas_used=sorted(set(schemas_used))
        )
    )

    for path, methods in paths.items():
        for method, endpoint in methods.items():
            operation_id = endpoint.operationId
            if not operation_id:
                log.warning(f"Operation ID is missing for path: {path}")
                continue

            description = sanitize_text(str(endpoint.summary))
            resource_path = convert_path_params(path)
            function_definition = FunctionDefinition()
            is_paginated = collect_params(
                spec, operation_id, endpoint.parameters or [], function_definition
            )
            collect_request_body_params(
                spec, operation_id, endpoint.requestBody, function_definition, schema_registry
            )
            if is_paginated:
                collect_pagination_params(operation_id, function_definition)
            is_paginated = check_force_paginated(
                operation_id=operation_id,
                is_paginated=is_paginated,
                function_definition=function_definition,
                force_paginated=force_paginated,
            )

            # Track if endpoint originally had pagination params (for template)
            has_pagination_params = is_paginated

            response_schema_name = None
            item_schema_name = None
            has_untyped_response = operation_id in schema_registry.untyped_response_ops
            if method != "delete":
                schema_name = get_response_schema_name(operation_id)
                if schema_name in schema_registry.schema_names:
                    response_schema_name = schema_name
                    # For paginated endpoints, use first item schema from map or fallback to response schema
                    # (some OpenAPI specs incorrectly define array responses as objects)
                    if is_paginated:
                        item_schemas = schema_registry.item_schema_map.get(schema_name)
                        item_schema_name = item_schemas[0] if item_schemas else schema_name

            is_list_response = (
                response_schema_name is not None
                and response_schema_name in schema_registry.list_response_schemas
            )
            if is_list_response and not is_paginated and method == "get":
                is_paginated = True
                # Get item schema for list response
                assert response_schema_name is not None
                item_schemas = schema_registry.item_schema_map.get(response_schema_name)
                item_schema_name = item_schemas[0] if item_schemas else response_schema_name

            definition = build_function_definition(
                function_definition.required_args, function_definition.optional_args
            )

            if is_paginated and not item_schema_name:
                raise ValueError(f"Paginated endpoint {operation_id} has no response schema")

            if method != "delete" and not response_schema_name and not has_untyped_response:
                responses = endpoint.responses or {}
                if "200" in responses or "201" in responses:
                    raise ValueError(f"Endpoint {operation_id} has 200/201 response but no schema")

            body_params_for_template = [
                (bp.snake_name, bp.orig_name, bp.is_schema, bp.is_list, bp.is_dict)
                for bp in function_definition.body_params
            ]

            return_description, response_example = get_response_info(endpoint)
            use_raw_docstring = response_example is not None and "\\" in response_example

            common_params = {
                "function_name": to_snake_case(operation_id),
                "operation_id": operation_id,
                "function_definition": definition,
                "description": description,
                "doc_url": docs_url(operation_id),
                "descriptions": function_definition.param_descriptions,
                "assert_blocks": function_definition.assert_blocks,
                "resource": resource_path,
                "query_params": function_definition.query_params,
                "body_params": body_params_for_template,
                "path_params": function_definition.path_params,
                "response_schema_name": response_schema_name,
                "item_schema_name": item_schema_name,
                "return_description": return_description,
                "response_example": response_example,
                "use_raw_docstring": use_raw_docstring,
            }

            output.write(
                templates.function_template.render(
                    **common_params,
                    method=method,
                    scope=scope,
                    return_type=get_return_type(
                        method=method,
                        is_paginated=is_paginated,
                        is_async=False,
                        response_schema_name=response_schema_name,
                        item_schema_name=item_schema_name,
                        has_untyped_response=has_untyped_response,
                    ),
                    is_async=False,
                    is_paginated=is_paginated,
                    has_pagination_params=has_pagination_params,
                )
            )
            async_output.write(
                templates.function_template.render(
                    **common_params,
                    method=method,
                    scope=scope,
                    return_type=get_return_type(
                        method=method,
                        is_paginated=is_paginated,
                        is_async=True,
                        response_schema_name=response_schema_name,
                        item_schema_name=item_schema_name,
                        has_untyped_response=has_untyped_response,
                    ),
                    is_async=True,
                    is_paginated=is_paginated,
                    has_pagination_params=has_pagination_params,
                )
            )

            batch_operation = batchable_actions_map.get(endpoint.description or "")
            if batch_operation:
                batch_schemas_used.extend(function_definition.request_body_schemas_used)

                batch_content.append(
                    templates.batch_function_template.render(
                        operation_id=operation_id,
                        function_name=to_snake_case(operation_id),
                        function_definition=definition,
                        description=description,
                        doc_url=docs_url(operation_id),
                        descriptions=function_definition.param_descriptions,
                        assert_blocks=function_definition.assert_blocks,
                        resource=resource_path,
                        query_params=function_definition.query_params,
                        body_params=body_params_for_template,
                        path_params=function_definition.path_params,
                        batch_operation=batch_operation,
                    )
                )

    if batch_content:
        return templates.batch_class_template.render(
            class_name=class_name, schemas_used=sorted(set(batch_schemas_used))
        ) + "".join(batch_content)
    return None


def generate_api_reference_docs(
    scopes: list[str] | KeysView[str],
    templates: Templates,
) -> None:
    """Generate API reference markdown docs for mkdocs."""
    os.makedirs(DOCS_DIR, exist_ok=True)

    # Generate module docs
    for scope in scopes:
        module_name = to_snake_case(scope)
        title = MODULE_DISPLAY_TITLES.get(scope, capitalize_first(scope))
        content = templates.api_reference_template.render(
            title=title,
            module_path=f"meraki_client._api.{module_name}.{capitalize_first(scope)}",
        )
        with open(f"{DOCS_DIR}/{module_name}.md", "w") as f:
            f.write(content)


def build_function_definition(required_args: list[str], optional_args: list[str]) -> str:
    """Build function definition string with appropriate positional/keyword-only parameters.

    If there's exactly one required parameter, it's positional. All other parameters
    (including optional and multiple required) are keyword-only.
    """
    if not required_args and not optional_args:
        return ""

    if len(required_args) == 1:
        # Single required param is positional, optional params are keyword-only
        if optional_args:
            return f", {required_args[0]}, *, " + ", ".join(optional_args)
        return f", {required_args[0]}"

    # Multiple required or no required: all keyword-only
    all_args = required_args + optional_args
    return ", *, " + ", ".join(all_args)


def recreate_output_directory() -> None:
    """Recreate the output directory."""
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)

    subdirs = [
        OUTPUT_DIR,
        f"{OUTPUT_DIR}/_api",
        f"{OUTPUT_DIR}/_api/batch",
        f"{OUTPUT_DIR}/aio",
        f"{OUTPUT_DIR}/aio/_api",
        f"{OUTPUT_DIR}/schemas",
    ]
    for directory in subdirs:
        os.makedirs(directory, exist_ok=True)


def copy_static_files() -> None:
    """Copy static files from the static directory to the output directory."""
    static_dir = Path(SCRIPT_DIR) / "static"
    for src in static_dir.rglob("*"):
        if src.is_file():
            relative_path = src.relative_to(static_dir)
            dst = Path(OUTPUT_DIR) / relative_path
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)


def _format_generated_code(output_dir: str) -> None:
    subprocess.run(  # noqa: S603
        ["uv", "run", "ruff", "check", "--quiet", "--select", "I,F401,RUF022", "--fix", output_dir],  # noqa: S607
        check=True,
    )
    subprocess.run(  # noqa: S603
        ["uv", "run", "ruff", "format", "--quiet", output_dir],  # noqa: S607
        check=True,
    )


def init_templates() -> Templates:
    """Initialize the templates."""
    jinja_env = jinja2.Environment(trim_blocks=True, lstrip_blocks=True, keep_trailing_newline=True)  # noqa: S701
    return Templates(
        api_reference_template=read_template("api_reference_template.md", jinja_env),
        batch_class_template=read_template("batch_class_template.py", jinja_env),
        batch_function_template=read_template("batch_function_template.py", jinja_env),
        batch_init_template=read_template("batch_init_template.py", jinja_env),
        class_template=read_template("class_template.py", jinja_env),
        function_template=read_template("function_template.py", jinja_env),
        init_template=read_template("init_template.py", jinja_env),
        schema_base_template=read_template("schema_base_template.py", jinja_env),
        schema_init_template=read_template("schema_init_template.py", jinja_env),
        schema_module_template=read_template("schema_module_template.py", jinja_env),
        session_template=read_template("session_template.py", jinja_env),
    )


def read_template(template_name: str, jinja_env: jinja2.Environment) -> jinja2.Template:
    """Read a template from the template directory."""
    with open(
        os.path.join(TEMPLATE_DIR, f"{template_name}.jinja2"), encoding="utf-8", newline=None
    ) as fp:
        return jinja_env.from_string(fp.read())


def collect_params(
    spec: OpenAPI,
    operation_id: str,
    parameters: list[Parameter | Reference],
    function_definition: FunctionDefinition,
) -> bool:
    """Collect path and query parameters. Returns True if paginated."""
    is_paginated = False
    for param in parameters:
        if isinstance(param, Reference):
            param = resolve_ref(spec, param, Parameter)  # noqa: PLW2901
            if not param:
                log.warning(f"Failed to resolve parameter reference: {param}")
                continue

        param_name = param.name
        snake_name = escape_reserved_name(to_snake_case(param_name))

        param_schema = param.param_schema
        if not param_schema:
            log.warning(f"No schema found for parameter: {param_name}")
            continue
        if isinstance(param_schema, Reference):
            param_schema = resolve_ref(spec, param_schema, Schema)
            if not param_schema:
                log.error(f"Failed to resolve schema reference: {param_schema}")
                continue

        py_type = get_python_type(param_schema)

        if param.param_in == ParameterLocation.QUERY:
            key = param_name
            if param_schema.type == DataType.ARRAY:
                # Query parameter syntax for arrays is param[]=value
                key += "[]"
            function_definition.query_params.append((snake_name, key))
        elif param.param_in == ParameterLocation.PATH:
            function_definition.path_params.append(snake_name)
        else:
            log.error(
                f"Unsupported parameter location '{param.param_in}' for operation: {operation_id}"
            )
            continue

        function_definition.param_descriptions.append(
            format_param_description(
                snake_name, param.description or param_schema.description or ""
            )
        )

        if snake_name == "per_page":
            is_paginated = True

        if param.required or param.param_in == ParameterLocation.PATH:
            function_definition.required_args.append(f"{snake_name}: {py_type}")
        else:
            function_definition.optional_args.append(f"{snake_name}: {py_type} | None = None")
        if param_schema.enum:
            function_definition.assert_blocks.append((snake_name, param_schema.enum))

    return is_paginated


def collect_request_body_params(
    spec: OpenAPI,
    operation_id: str,
    request_body: RequestBody | Reference | None,
    function_definition: FunctionDefinition,
    schema_registry: SchemaRegistry,
) -> None:
    """Collect request body parameters."""
    if isinstance(request_body, Reference):
        request_body = resolve_ref(spec, request_body, RequestBody)

    if not request_body:
        return

    json_content = request_body.content.get("application/json")
    if not json_content:
        log.warning(f"No JSON content found in request body for operation: {operation_id}")
        return

    content_schema = json_content.media_type_schema
    if isinstance(content_schema, Reference):
        content_schema = resolve_ref(spec, content_schema, Schema)
    if not content_schema:
        log.warning(f"No schema found in request body for operation: {operation_id}")
        return

    properties = content_schema.properties or {}
    for property_name, property_schema in properties.items():
        snake_name = escape_reserved_name(to_snake_case(property_name))
        if isinstance(property_schema, Reference):
            property_schema = resolve_ref(spec, property_schema, Schema)  # noqa: PLW2901
            if not property_schema:
                log.error(f"Failed to resolve schema reference: {property_schema}")
                continue

        schema_key = (operation_id, property_name)
        param_schema = schema_registry.request_body_schemas.get(schema_key)

        is_schema = param_schema is not None
        is_list = param_schema.is_list if param_schema else False
        is_dict = param_schema.is_dict if param_schema else False
        function_definition.body_params.append(
            BodyParam(snake_name, property_name, is_schema, is_list, is_dict)
        )

        if (
            property_name == "scheduleId"
            and operation_id == "deleteOrganizationDevicesPacketCaptureSchedule"
        ):
            # Schedule ID is duplicate of path param in this operation
            continue

        function_definition.param_descriptions.append(
            format_param_description(snake_name, property_schema.description or "")
        )

        if param_schema:
            py_type = param_schema.class_name
            if param_schema.item_class_name:
                function_definition.request_body_schemas_used.append(param_schema.item_class_name)
            elif not param_schema.is_list:
                function_definition.request_body_schemas_used.append(param_schema.class_name)
        else:
            py_type = get_python_type(property_schema)

        required_properties = content_schema.required or []
        if property_name in required_properties:
            function_definition.required_args.append(f"{snake_name}: {py_type}")
        else:
            function_definition.optional_args.append(f"{snake_name}: {py_type} | None = None")

        if property_schema.enum:
            function_definition.assert_blocks.append((snake_name, property_schema.enum))


def check_force_paginated(
    *,
    operation_id: str,
    is_paginated: bool,
    function_definition: FunctionDefinition,
    force_paginated: set[str],
) -> bool:
    """Check if endpoint should be force-paginated due to spec bugs.

    Returns True if endpoint should be treated as paginated.
    Logs warning if endpoint appears to be fixed in spec.
    """
    if operation_id not in force_paginated:
        return is_paginated

    if is_paginated:
        log.warning(
            f"{operation_id} in force_paginated now has per_page param - "
            "spec may be fixed, check if override still needed"
        )
    else:
        is_paginated = True
        collect_pagination_params(operation_id, function_definition)

    return is_paginated


def collect_pagination_params(operation_id: str, function_definition: FunctionDefinition) -> None:
    """Collect pagination parameters."""
    function_definition.optional_args.append('total_pages: int | Literal["all"] = "all"')

    function_definition.param_descriptions.append(
        format_param_description(
            "total_pages",
            "use with per_page to get total results"
            ' up to total_pages * per_page; -1 or "all" for all pages',
        )
    )

    if operation_id in REVERSE_PAGINATION:
        function_definition.optional_args.append("direction: Literal['prev', 'next'] = 'prev'")
    else:
        function_definition.optional_args.append("direction: Literal['prev', 'next'] = 'next'")

    function_definition.param_descriptions.append(
        format_param_description(
            "direction",
            'direction to paginate, either "next" or "prev" (default) page'
            if operation_id in REVERSE_PAGINATION
            else 'direction to paginate, either "next" (default) or "prev" page',
        )
    )

    if operation_id == "getNetworkEvents":
        function_definition.optional_args.append("event_log_end_time: str | None = None")
        function_definition.param_descriptions.append(
            format_param_description(
                "event_log_end_time",
                "ISO8601 Zulu/UTC time, to use in conjunction with starting_after, "
                "to retrieve events within a time window",
            )
        )


def get_return_type(
    *,
    method: Literal["get", "put", "post", "delete"],
    is_paginated: bool,
    is_async: bool,
    response_schema_name: str | None = None,
    item_schema_name: str | None = None,
    has_untyped_response: bool = False,
) -> str:
    """Get the return type for a function."""
    if method == "delete":
        return "None"
    if method == "get" and is_paginated and item_schema_name:
        return (
            f"AsyncPaginatedResponse[{item_schema_name}]"
            if is_async
            else f"PaginatedResponse[{item_schema_name}]"
        )
    if response_schema_name:
        return f"{response_schema_name} | None"
    if has_untyped_response:
        return "dict[str, Any] | None"
    return "None"


def get_response_info(endpoint: Operation) -> tuple[str | None, str | None]:
    """Get the return description and example from the OpenAPI response."""
    responses = endpoint.responses or {}
    for status_code, response in responses.items():
        if not status_code.startswith("2"):
            continue
        if isinstance(response, Reference):
            continue

        description = sanitize_text(response.description) if response.description else None

        example = None
        content = response.content
        if content:
            json_content = content.get("application/json")
            if json_content and json_content.example:
                example = json.dumps(json_content.example, indent=2)

        return description, example

    return None, None


def format_param_description(name: str, description: str) -> str:
    """Format a parameter description for Google-style docstring with line wrapping."""
    first_line = f"{name}: {sanitize_text(description)}"
    if len(first_line) <= DOCSTRING_LINE_WIDTH:
        return first_line

    wrapper = textwrap.TextWrapper(
        width=DOCSTRING_LINE_WIDTH,
        initial_indent="",
        subsequent_indent=" " * (INDENT_WIDTH + 4),
    )
    return wrapper.fill(first_line)


_T = TypeVar("_T")


def resolve_ref(
    spec: OpenAPI,
    ref: Reference,
    expected_type: type[_T],
    _seen: set[str] | None = None,
) -> _T | None:
    """Resolve a $ref reference in OASv3 spec."""
    ref_str = ref.ref
    if not ref_str.startswith("#/"):
        # Ignore external refs
        return None

    if _seen is None:
        _seen = set()
    if ref_str in _seen:
        return None
    _seen = _seen | {ref_str}

    parts = [unquote(p) for p in ref_str[2:].split("/")]

    result: Any = spec
    for part in parts:
        if isinstance(result, dict):
            if part in result:
                result = result[part]
            else:
                return None
        elif isinstance(result, BaseModel):
            if hasattr(result, part):
                result = getattr(result, part)
            else:
                found = False
                for field_name, field_info in type(result).model_fields.items():
                    if field_info.alias == part:
                        result = getattr(result, field_name)
                        found = True
                        break
                if not found:
                    return None
        else:
            return None

    if isinstance(result, Reference):
        return resolve_ref(spec, result, expected_type, _seen)

    if isinstance(result, expected_type):
        return result
    return None


def docs_url(operation_id: str) -> str:
    """Returns full link to endpoint's documentation on Developer Hub."""
    base_url = "https://developer.cisco.com/meraki/api-v1/#!"
    kebab = to_snake(operation_id).replace("_", "-")
    # Insert hyphen between letter and digit: l3 -> l-3, hotspot20 -> hotspot-20
    kebab = re.sub(r"([a-z])(\d)", r"\1-\2", kebab)
    return base_url + kebab


def convert_path_params(path: str) -> str:
    """Convert all {paramName} in path to {param_name} (snake_case, sanitized)."""

    def replace_param(match: re.Match[str]) -> str:
        param = match.group(1)
        return f"{{{escape_reserved_name(to_snake_case(param))}}}"

    return re.sub(r"\{(\w+)\}", replace_param, path)


def get_python_type(schema: Schema) -> str:
    """Get Python type for a schema."""
    data_type = schema.type or DataType.STRING
    match data_type:
        case DataType.ARRAY:
            items = schema.items
            if items and isinstance(items, Schema) and items.type:
                item_type = _get_simple_type(items.type)
                return f"list[{item_type}]"
            log.warning(f"Unknown array items type: {items}")
            return "list[Any]"
        case DataType.NUMBER:
            return "float"
        case DataType.INTEGER:
            return "int"
        case DataType.BOOLEAN:
            return "bool"
        case DataType.OBJECT:
            return "dict[str, Any]"
        case DataType.STRING:
            return "str"
        case _:
            assert_never(data_type)


def _get_simple_type(data_type: DataType) -> str:
    """Get Python type string for a simple data type."""
    match data_type:
        case DataType.STRING:
            return "str"
        case DataType.INTEGER:
            return "int"
        case DataType.NUMBER:
            return "float"
        case DataType.BOOLEAN:
            return "bool"
        case DataType.OBJECT:
            return "dict"
        case DataType.ARRAY:
            return "list"
        case _:
            assert_never(data_type)


if __name__ == "__main__":
    main()
