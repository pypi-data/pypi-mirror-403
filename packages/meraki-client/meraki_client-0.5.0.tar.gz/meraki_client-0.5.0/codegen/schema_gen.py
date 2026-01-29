"""Pydantic schema generation from OpenAPI specification."""

from __future__ import annotations

import json
import logging
import re
import textwrap
from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING, Any, Literal, NamedTuple, overload

from openapi_pydantic.v3.v3_0 import OpenAPI, Operation, Reference

from codegen.utils import (
    SpecOverrides,
    capitalize_first,
    escape_reserved_name,
    load_spec_overrides,
    sanitize_text,
    to_snake_case,
)

if TYPE_CHECKING:
    from codegen.main import Templates

log = logging.getLogger("codegen")

SCHEMA_DOCSTRING_WIDTH = 96
MAX_CLASS_NAME_LENGTH = 80
TYPE_MAP = {"string": "str", "integer": "int", "number": "float", "boolean": "bool"}
FORMAT_MAP = {
    "date-time": "datetime",
    "date": "date",
    "time": "time",
    "byte": "str",  # base64 encoded, keep as string
    "float": "float",  # redundant with type: number
}


class SchemaStatus(Enum):
    """Result status for schema generation."""

    GENERATED = auto()  # New schema was created
    DEDUPED = auto()  # Schema already existed (same definition)
    SKIPPED = auto()  # Schema couldn't be generated (no properties, wrong type, etc.)


@dataclass
class SchemaResult:
    """Result of schema generation."""

    status: SchemaStatus
    class_name: str | None = None
    is_array: bool = False
    item_class_names: list[str] | None = None


@dataclass
class RequestBodyParamSchema:
    """Schema info for a request body parameter."""

    class_name: str
    is_list: bool = False
    is_dict: bool = False
    item_class_name: str | None = None


@dataclass
class SchemaRegistry:
    """Registry of generated response schemas."""

    schema_names: set[str]
    item_schema_map: dict[str, list[str]]
    untyped_response_ops: set[str]
    # Map of (operation_id, property_name) -> RequestBodyParamSchema
    request_body_schemas: dict[tuple[str, str], RequestBodyParamSchema]
    # Set of response schema names that are list types
    list_response_schemas: set[str]


@dataclass
class GenerationContext:
    """Context for schema generation carrying shared state."""

    schemas: dict[str, str]
    schema_to_scope: dict[str, str]
    schema_fingerprints: dict[str, str]
    scope: str
    depth: int = 0
    operation_id: str | None = None
    field_path: tuple[str, ...] = ()
    spec_overrides: SpecOverrides | None = None
    consumed_overrides: set[tuple[str, str]] | None = None
    consumed_required_overrides: set[tuple[str, str]] | None = None

    def nested(self, path_segment: str | None = None) -> GenerationContext:
        """Create a new context for nested schema generation."""
        new_path = (*self.field_path, path_segment) if path_segment else self.field_path
        return GenerationContext(
            schemas=self.schemas,
            schema_to_scope=self.schema_to_scope,
            schema_fingerprints=self.schema_fingerprints,
            scope=self.scope,
            depth=self.depth + 1,
            operation_id=self.operation_id,
            field_path=new_path,
            spec_overrides=self.spec_overrides,
            consumed_overrides=self.consumed_overrides,
            consumed_required_overrides=self.consumed_required_overrides,
        )


class TypeResult(NamedTuple):
    """Result of type resolution, optionally including nested item class."""

    type_str: str
    item_class: str | None = None


def get_response_schema_name(operation_id: str) -> str:
    """Get the response schema class name for an operation."""
    return f"{capitalize_first(operation_id)}Response"


def get_request_param_schema_name(operation_id: str, property_name: str) -> str:
    """Get the request body parameter schema class name."""
    parts = re.split(r"[/_]", property_name)
    sanitized_prop = "".join(capitalize_first(p) if p else "" for p in parts)
    return f"{capitalize_first(operation_id)}{sanitized_prop}"


def generate_response_schemas(
    spec: OpenAPI, templates: Templates, output_dir: str
) -> SchemaRegistry:
    """Generate Pydantic response and request body schemas from OpenAPI specification."""
    schemas: dict[str, str] = {}
    schema_to_scope: dict[str, str] = {}
    schema_fingerprints: dict[str, str] = {}
    item_schema_map: dict[str, list[str]] = {}
    untyped_response_operations: set[str] = set()
    request_body_schemas: dict[tuple[str, str], RequestBodyParamSchema] = {}
    list_response_schemas: set[str] = set()

    spec_overrides = load_spec_overrides()
    consumed_overrides: set[tuple[str, str]] = set()
    consumed_required_overrides: set[tuple[str, str]] = set()
    spec_operation_ids: set[str] = set()

    for path_item in spec.paths.values():
        operations: dict[Literal["get", "put", "post", "delete"], Operation | None] = {
            "get": path_item.get,
            "put": path_item.put,
            "post": path_item.post,
            "delete": path_item.delete,
        }
        for operation in operations.values():
            if not operation or not operation.operationId:
                continue

            operation_id = operation.operationId
            spec_operation_ids.add(operation_id)
            scope = operation.tags[0] if operation.tags else None
            if not scope:
                log.warning(f"Operation {operation_id} has no tags")
                continue

            ctx = GenerationContext(
                schemas=schemas,
                schema_to_scope=schema_to_scope,
                schema_fingerprints=schema_fingerprints,
                scope=scope,
                operation_id=operation_id,
                spec_overrides=spec_overrides,
                consumed_overrides=consumed_overrides,
                consumed_required_overrides=consumed_required_overrides,
            )

            # Generate response schemas
            response_schema = _extract_response_schema(operation)
            if response_schema:
                response_schema = _apply_force_array_response(
                    operation_id, response_schema, spec_overrides.force_array_response
                )
                class_name = get_response_schema_name(operation_id)
                result = _generate_schema_class(
                    ctx,
                    class_name=class_name,
                    schema=response_schema,
                    description=f"Response for {operation_id} operation.",
                )
                if result.status != SchemaStatus.SKIPPED:
                    if result.item_class_names:
                        item_schema_map[class_name] = result.item_class_names
                    if result.is_array:
                        list_response_schemas.add(class_name)
                else:
                    untyped_response_operations.add(operation_id)

            # Generate request body schemas
            _generate_request_body_schemas(
                ctx,
                operation=operation,
                request_body_schemas=request_body_schemas,
            )

    _validate_spec_overrides(
        spec_overrides, consumed_overrides, consumed_required_overrides, spec_operation_ids
    )

    _write_schema_files(
        schemas=schemas,
        schema_to_scope=schema_to_scope,
        templates=templates,
        output_dir=output_dir,
    )
    return SchemaRegistry(
        schema_names=set(schemas.keys()),
        item_schema_map=item_schema_map,
        untyped_response_ops=untyped_response_operations,
        request_body_schemas=request_body_schemas,
        list_response_schemas=list_response_schemas,
    )


def _generate_request_body_schemas(
    ctx: GenerationContext,
    *,
    operation: Operation,
    request_body_schemas: dict[tuple[str, str], RequestBodyParamSchema],
) -> None:
    """Generate schemas for request body parameters that are objects or arrays."""
    operation_id = operation.operationId
    if not operation_id:
        return

    request_body = operation.requestBody
    if not request_body:
        return

    if isinstance(request_body, Reference):
        raise ValueError(f"Operation {operation_id} has a reference request body")

    json_content = request_body.content.get("application/json")
    if not json_content:
        raise ValueError(f"Operation {operation_id} has no JSON content")

    content_schema = json_content.media_type_schema
    if isinstance(content_schema, Reference) or not content_schema:
        raise ValueError(f"Operation {operation_id} has no schema or schema is a reference")

    properties = content_schema.properties or {}
    for property_name, property_schema in properties.items():
        if isinstance(property_schema, Reference):
            raise ValueError(f"Operation {operation_id} has a reference property: {property_name}")

        schema_dict = property_schema.model_dump(exclude_none=True)
        base_class_name = get_request_param_schema_name(operation_id, property_name)

        param_schema = _generate_request_body_param_schema(
            ctx,
            base_class_name=base_class_name,
            schema_dict=schema_dict,
            property_name=property_name,
        )
        if param_schema:
            request_body_schemas[(operation_id, property_name)] = param_schema


def _generate_request_body_param_schema(
    ctx: GenerationContext,
    *,
    base_class_name: str,
    schema_dict: dict[str, Any],
    property_name: str,
) -> RequestBodyParamSchema | None:
    """Generate schema for a single request body parameter if it's a complex type."""
    schema_type = schema_dict.get("type")

    if schema_type == "object":
        return _generate_request_body_object_schema(
            ctx,
            base_class_name=base_class_name,
            schema_dict=schema_dict,
            property_name=property_name,
        )
    if schema_type == "array":
        return _generate_request_body_array_schema(
            ctx,
            base_class_name=base_class_name,
            schema_dict=schema_dict,
            property_name=property_name,
        )
    return None


def _generate_request_body_object_schema(
    ctx: GenerationContext,
    *,
    base_class_name: str,
    schema_dict: dict[str, Any],
    property_name: str,
) -> RequestBodyParamSchema | None:
    """Generate schema for an object-type request body parameter."""
    if schema_dict.get("properties"):
        result = _generate_schema_class(ctx, class_name=base_class_name, schema=schema_dict)
        if result.status != SchemaStatus.SKIPPED:
            return RequestBodyParamSchema(class_name=result.class_name or base_class_name)
        return None

    additional_props = schema_dict.get("additionalProperties")
    if isinstance(additional_props, dict) and _has_nested_properties(additional_props):
        value_class_name = base_class_name + "Value"
        result = _generate_schema_class(
            ctx,
            class_name=value_class_name,
            schema=additional_props,
            description=f"Value schema for {property_name}.",
        )
        if result.status != SchemaStatus.SKIPPED:
            return RequestBodyParamSchema(
                class_name=f"dict[str, {result.class_name or value_class_name}]",
                is_dict=True,
                item_class_name=result.class_name or value_class_name,
            )
    return None


def _generate_request_body_array_schema(
    ctx: GenerationContext,
    *,
    base_class_name: str,
    schema_dict: dict[str, Any],
    property_name: str,
) -> RequestBodyParamSchema | None:
    """Generate schema for an array-type request body parameter."""
    items = schema_dict.get("items", {})
    if not _has_nested_properties(items):
        return None

    item_class_name = base_class_name + "Item"
    result = _generate_schema_class(
        ctx,
        class_name=item_class_name,
        schema=items,
        description=f"Item schema for {property_name}.",
    )
    if result.status != SchemaStatus.SKIPPED:
        return RequestBodyParamSchema(
            class_name=f"list[{result.class_name or item_class_name}]",
            is_list=True,
            item_class_name=result.class_name or item_class_name,
        )
    return None


def _apply_force_array_response(
    operation_id: str, schema: dict[str, Any], force_array_response: set[str]
) -> dict[str, Any]:
    """Apply force_array_response override if needed.

    For endpoints where spec says object but API returns array.
    Logs warning if endpoint appears to be fixed in spec.
    """
    if operation_id not in force_array_response:
        return schema

    if schema.get("type") == "array":
        log.warning(
            f"{operation_id} in force_array_response already has array schema - "
            "spec may be fixed, check if override still needed"
        )
        return schema

    # Wrap object schema in array
    return {"type": "array", "items": schema}


def _extract_response_schema(operation: Operation) -> dict[str, Any] | None:
    """Extract the response schema from the operation's 2xx response."""
    found_schema: dict[str, Any] | None = None
    found_status: str | None = None

    for status_code, response in operation.responses.items():
        if not status_code.startswith("2"):
            continue
        if isinstance(response, Reference):
            raise ValueError(
                f"Operation {operation.operationId} has a reference response for {status_code}"
            )

        content = response.content
        if not content:
            if status_code not in ["202", "204"]:
                log.warning(f"Operation {operation.operationId} has no content for {status_code}")
            continue

        json_content = content.get("application/json")
        if not json_content:
            log.warning(f"Operation {operation.operationId} has no JSON content for {status_code}")
            continue

        schema = json_content.media_type_schema
        if not schema:
            log.warning(f"Operation {operation.operationId} has no schema for {status_code}")
            continue
        if isinstance(schema, Reference):
            raise ValueError(
                f"Operation {operation.operationId} has a reference schema for {status_code}"
            )
        if found_schema is not None:
            raise ValueError(
                f"Operation {operation.operationId} has multiple 2xx responses "
                f"with schemas: {found_status} and {status_code}"
            )
        found_schema = schema.model_dump(exclude_none=True)
        found_status = status_code

    return found_schema


def _generate_schema_class(
    ctx: GenerationContext,
    *,
    class_name: str,
    schema: dict[str, Any],
    description: str | None = None,
) -> SchemaResult:
    """Generate a Pydantic model class from an OpenAPI schema."""
    schema_type = schema.get("type")
    docstring = schema.get("description") or description or f"Schema for {class_name}."

    if schema_type == "array":
        return _generate_array_schema(
            ctx, class_name=class_name, schema=schema, docstring=docstring
        )

    if schema_type == "object" or "properties" in schema:
        return _generate_object_schema(
            ctx, class_name=class_name, schema=schema, docstring=docstring
        )
    log.warning(f"Skipping schema generation for {class_name} because it has no properties")
    return SchemaResult(status=SchemaStatus.SKIPPED)


def _generate_array_schema(
    ctx: GenerationContext,
    *,
    class_name: str,
    schema: dict[str, Any],
    docstring: str,
) -> SchemaResult:
    """Generate a RootModel schema for array responses."""
    items_schema = schema.get("items", {})
    should_generate_nested = items_schema.get("type") == "object"
    inner_type, nested_class = _resolve_inner_type(
        ctx,
        inner_schema=items_schema,
        nested_class_name=class_name + "Item",
        should_generate_nested=should_generate_nested,
    )
    return _build_root_model_result(
        ctx,
        class_name=class_name,
        root_type=f"list[{inner_type}]",
        docstring=docstring,
        is_array=True,
        nested_class=nested_class,
    )


def _generate_dict_schema(
    ctx: GenerationContext,
    *,
    class_name: str,
    value_schema: dict[str, Any],
    docstring: str,
) -> SchemaResult:
    """Generate a RootModel schema for dict/map responses with additionalProperties."""
    should_generate_nested = _has_nested_properties(value_schema)
    inner_type, nested_class = _resolve_inner_type(
        ctx,
        inner_schema=value_schema,
        nested_class_name=class_name + "Value",
        should_generate_nested=should_generate_nested,
    )
    return _build_root_model_result(
        ctx,
        class_name=class_name,
        root_type=f"dict[str, {inner_type}]",
        docstring=docstring,
        is_array=False,
        nested_class=nested_class,
    )


def _resolve_inner_type(
    ctx: GenerationContext,
    *,
    inner_schema: dict[str, Any],
    nested_class_name: str,
    should_generate_nested: bool,
) -> tuple[str, str | None]:
    """Resolve the inner type for a RootModel container.

    Returns (type_string, nested_class_name_if_generated).
    """
    if should_generate_nested:
        result = _generate_schema_class(
            ctx.nested(), class_name=nested_class_name, schema=inner_schema
        )
        if result.status != SchemaStatus.SKIPPED:
            return f'"{nested_class_name}"', nested_class_name
        return "dict[str, Any]", None

    return _get_simple_type(inner_schema), None


def _build_root_model_result(
    ctx: GenerationContext,
    *,
    class_name: str,
    root_type: str,
    docstring: str,
    is_array: bool,
    nested_class: str | None,
) -> SchemaResult:
    """Build and register a RootModel schema, returning the result."""
    doc_lines = _format_docstring(docstring)
    body = "" if doc_lines else "    pass\n"
    definition = f"class {class_name}(RootModel[{root_type}]):\n{doc_lines}{body}"

    status = _register_schema(ctx, name=class_name, definition=definition)
    return SchemaResult(
        status=status,
        class_name=class_name,
        is_array=is_array,
        item_class_names=[nested_class] if nested_class else None,
    )


def _generate_object_schema(
    ctx: GenerationContext,
    *,
    class_name: str,
    schema: dict[str, Any],
    docstring: str,
) -> SchemaResult:
    """Generate a _BaseSchema class for object responses."""
    properties = schema.get("properties", {})

    if not properties:
        additional_props = schema.get("additionalProperties")
        if not isinstance(additional_props, dict):
            log.debug(
                f"Skipping schema generation for {class_name} "
                "because it has no properties or additional properties"
            )
            return SchemaResult(status=SchemaStatus.SKIPPED)
        return _generate_dict_schema(
            ctx, class_name=class_name, value_schema=additional_props, docstring=docstring
        )

    lines = [f"class {class_name}(_BaseSchema):"]
    if docstring:
        lines.extend(_format_docstring(docstring, as_lines=True))

    required = set(schema.get("required", []))
    item_class_names: list[str] = []

    for prop_name, prop_schema in properties.items():
        is_required_in_spec = prop_name in required
        is_force_required = _is_field_force_required(
            ctx, prop_name, is_required_in_spec=is_required_in_spec
        )
        field_def, item_class = _generate_field(
            ctx,
            parent_class=class_name,
            prop_name=prop_name,
            prop_schema=prop_schema,
            is_required=is_required_in_spec or is_force_required,
        )
        lines.append(f"    {field_def}")
        if item_class:
            item_class_names.append(item_class)

    status = _register_schema(ctx, name=class_name, definition="\n".join(lines) + "\n")
    return SchemaResult(
        status=status,
        class_name=class_name,
        is_array=False,
        item_class_names=item_class_names or None,
    )


def _register_schema(ctx: GenerationContext, *, name: str, definition: str) -> SchemaStatus:
    """Register a schema. Returns GENERATED if new, DEDUPED if already exists."""
    if name in ctx.schemas:
        existing_scope = ctx.schema_to_scope.get(name)
        if existing_scope != ctx.scope:
            raise ValueError(
                f"Schema name collision: '{name}' already exists in scope "
                f"'{existing_scope}', cannot add to scope '{ctx.scope}'"
            )
        if ctx.schemas[name] != definition:
            raise ValueError(
                f"Schema collision: '{name}' in scope '{ctx.scope}' has conflicting definitions"
            )
        return SchemaStatus.DEDUPED

    ctx.schemas[name] = definition
    ctx.schema_to_scope[name] = ctx.scope
    return SchemaStatus.GENERATED


def _get_field_override(
    ctx: GenerationContext, prop_name: str, prop_schema: dict[str, Any]
) -> str | None:
    """Check if there's a type override for this field and return the override type."""
    if not ctx.operation_id or ctx.spec_overrides is None or ctx.consumed_overrides is None:
        return None

    response_fields = ctx.spec_overrides.response_fields.get(ctx.operation_id)
    if not response_fields:
        return None

    field_path = ".".join((*ctx.field_path, prop_name))
    override_type = response_fields.get(field_path)
    if not override_type:
        return None

    spec_type = _get_simple_type(prop_schema)
    if spec_type == override_type:
        log.warning(
            f"{ctx.operation_id}: field '{field_path}' override type '{override_type}' "
            "matches spec type - spec may have been fixed"
        )

    ctx.consumed_overrides.add((ctx.operation_id, field_path))
    return override_type


def _is_field_force_required(
    ctx: GenerationContext, prop_name: str, *, is_required_in_spec: bool
) -> bool:
    """Check if a field should be forced as required via spec override.

    Returns True if there's an override marking this field as required.
    Logs a warning if the field is already required in the spec.
    """
    if (
        not ctx.operation_id
        or ctx.spec_overrides is None
        or ctx.consumed_required_overrides is None
    ):
        return False

    required_fields = ctx.spec_overrides.required_fields.get(ctx.operation_id)
    if not required_fields:
        return False

    field_path = ".".join((*ctx.field_path, prop_name))
    if field_path not in required_fields:
        return False

    if is_required_in_spec:
        log.warning(
            f"{ctx.operation_id}: field '{field_path}' is marked as required in override "
            "but is already required in spec - spec may have been fixed"
        )

    ctx.consumed_required_overrides.add((ctx.operation_id, field_path))
    return True


def _generate_field(
    ctx: GenerationContext,
    *,
    parent_class: str,
    prop_name: str,
    prop_schema: dict[str, Any],
    is_required: bool,
) -> tuple[str, str | None]:
    """Generate a field definition for a Pydantic model."""
    snake_name = _sanitize_field_name(prop_name)

    override_type = _get_field_override(ctx, prop_name, prop_schema)
    if override_type:
        type_str = override_type
        item_class = None
    else:
        type_str, item_class = _get_python_type(
            ctx, parent_class=parent_class, prop_name=prop_name, schema=prop_schema
        )

    needs_alias = snake_name != prop_name
    is_nullable = prop_schema.get("nullable", False)
    alias_args = f'validation_alias="{prop_name}", serialization_alias="{prop_name}"'

    if is_required:
        type_annotation = f"{type_str} | None" if is_nullable else type_str
        if needs_alias:
            return (
                f"{snake_name}: {type_annotation} = Field({alias_args})",
                item_class,
            )
        return f"{snake_name}: {type_annotation}", item_class

    if needs_alias:
        return (
            f"{snake_name}: {type_str} | None = Field(default=None, {alias_args})",
            item_class,
        )
    return f"{snake_name}: {type_str} | None = None", item_class


def _get_python_type(
    ctx: GenerationContext,
    *,
    parent_class: str,
    prop_name: str,
    schema: dict[str, Any],
) -> TypeResult:
    """Get Python type annotation from OpenAPI schema."""
    schema_type = schema.get("type")

    if schema_type in ("string", "integer", "number", "boolean"):
        return TypeResult(_get_simple_type(schema))

    if schema_type == "array":
        return _get_array_type(ctx, parent_class=parent_class, prop_name=prop_name, schema=schema)

    if schema_type == "object":
        return _get_object_type(ctx, parent_class=parent_class, prop_name=prop_name, schema=schema)

    log.warning(f"Unknown schema type: {schema_type}")
    return TypeResult("Any")


def _get_simple_type(schema: dict[str, Any]) -> str:
    """Get Python type for simple (non-class) schema types."""
    schema_type = schema.get("type")
    schema_format = schema.get("schema_format") or schema.get("format")
    if schema_format and schema_format not in FORMAT_MAP:
        log.warning(f"Unknown schema format: {schema_format}")
    if schema_type == "string" and schema_format in FORMAT_MAP:
        return FORMAT_MAP[schema_format]
    if schema_type in TYPE_MAP:
        return TYPE_MAP[schema_type]
    if schema_type == "array":
        item_type = _get_simple_type(schema.get("items", {}))
        return f"list[{item_type}]"
    if schema_type == "object":
        return "dict[str, Any]"
    log.warning(f"Unknown schema type: {schema_type}")
    return "Any"


def _get_array_type(
    ctx: GenerationContext,
    *,
    parent_class: str,
    prop_name: str,
    schema: dict[str, Any],
) -> TypeResult:
    """Get Python type for array schema."""
    items = schema.get("items", {})

    if _has_nested_properties(items):
        fingerprint = _compute_fingerprint(items, ctx.scope)
        if fingerprint in ctx.schema_fingerprints:
            existing_class = ctx.schema_fingerprints[fingerprint]
            return TypeResult(f"list[{existing_class}]", existing_class)

        nested_ctx = ctx.nested(prop_name)
        nested_class = _build_nested_class_name(
            nested_ctx, parent_class=parent_class, prop_name=prop_name, is_array=True
        )
        _generate_schema_class(nested_ctx, class_name=nested_class, schema=items)
        ctx.schema_fingerprints[fingerprint] = nested_class

        return TypeResult(f"list[{nested_class}]", nested_class)

    item_type = _get_simple_type(items)
    return TypeResult(f"list[{item_type}]")


def _get_object_type(
    ctx: GenerationContext,
    *,
    parent_class: str,
    prop_name: str,
    schema: dict[str, Any],
) -> TypeResult:
    """Get Python type for object schema."""
    props = schema.get("properties")

    if not props:
        return TypeResult("dict[str, Any]")

    fingerprint = _compute_fingerprint(schema, ctx.scope)
    if fingerprint in ctx.schema_fingerprints:
        return TypeResult(ctx.schema_fingerprints[fingerprint])

    nested_ctx = ctx.nested(prop_name)
    nested_class = _build_nested_class_name(
        nested_ctx, parent_class=parent_class, prop_name=prop_name, is_array=False
    )
    _generate_schema_class(nested_ctx, class_name=nested_class, schema=schema)
    ctx.schema_fingerprints[fingerprint] = nested_class

    return TypeResult(nested_class)


def _build_nested_class_name(
    ctx: GenerationContext,
    *,
    parent_class: str,
    prop_name: str,
    is_array: bool,
) -> str:
    """Build a nested class name with scope-aware shortening."""
    prop_pascal = capitalize_first(prop_name)
    suffix = "Item" if is_array else ""
    full_name = _sanitize_class_name(parent_class + prop_pascal + suffix)

    should_shorten = ctx.depth >= 2 or len(full_name) > MAX_CLASS_NAME_LENGTH
    if not should_shorten:
        return full_name

    scope_prefix = capitalize_first(ctx.scope)
    parent_context = ""
    if "Response" in parent_class:
        parent_context = parent_class.split("Response", 1)[-1]
        parent_context = re.sub(r"(Items?Item\d*|Item\d*)$", "", parent_context)

    base_short_name = _sanitize_class_name(f"{scope_prefix}{parent_context}{prop_pascal}{suffix}")

    if base_short_name not in ctx.schemas:
        return base_short_name

    for i in range(2, 100):
        numbered_name = f"{base_short_name}{i}"
        if numbered_name not in ctx.schemas:
            return numbered_name

    return full_name


def _has_nested_properties(schema: dict[str, Any]) -> bool:
    """Check if schema is an object with properties requiring a generated class."""
    return schema.get("type") == "object" and bool(schema.get("properties"))


def _sanitize_field_name(name: str) -> str:
    """Sanitize a field name to be a valid Python identifier."""
    if name and (name[0].isdigit() or name.replace(".", "").replace("-", "").isdigit()):
        return "n_" + name.replace(".", "_").replace("-", "_").replace("/", "_")
    if "/" in name:
        return escape_reserved_name(name.replace("/", "_").lower())
    return escape_reserved_name(to_snake_case(name))


def _sanitize_class_name(name: str) -> str:
    """Sanitize a class name to be a valid Python identifier."""
    parts = re.split(r"[/_]", name)
    name = "".join(capitalize_first(p) if p else "" for p in parts)
    return "N" + name if name and name[0].isdigit() else name


@overload
def _format_docstring(doc: str, *, as_lines: Literal[True]) -> list[str]: ...


@overload
def _format_docstring(doc: str, *, as_lines: Literal[False] = False) -> str: ...


def _format_docstring(doc: str, *, as_lines: bool = False) -> str | list[str]:
    """Format a docstring for a schema class with proper line wrapping."""
    if not doc:
        return [] if as_lines else ""

    doc = sanitize_text(doc)
    indent = "    "
    max_single_line = SCHEMA_DOCSTRING_WIDTH - len(indent) - 6

    if len(doc) <= max_single_line:
        line = f'{indent}"""{doc}"""'
        return [line, ""] if as_lines else f"{line}\n\n"

    wrapper = textwrap.TextWrapper(
        width=SCHEMA_DOCSTRING_WIDTH - len(indent),
        initial_indent="",
        subsequent_indent="",
    )
    wrapped_lines = wrapper.wrap(doc)

    lines = [f'{indent}"""{wrapped_lines[0]}']
    lines.extend(f"{indent}{wrapped}" for wrapped in wrapped_lines[1:])
    lines.append(f'{indent}"""')
    lines.append("")

    return lines if as_lines else "\n".join(lines) + "\n"


def _compute_fingerprint(schema: dict[str, Any], scope: str) -> str:
    """Compute a fingerprint for schema deduplication within a scope."""
    normalized = _normalize_schema(schema)
    return f"{scope}:{json.dumps(normalized, sort_keys=True)}"


def _normalize_schema(schema: dict[str, Any], *, is_required: bool = False) -> dict[str, Any]:
    """Normalize schema to only include fields that affect generated code structure."""
    result: dict[str, Any] = {}

    if "type" in schema:
        result["type"] = schema["type"]

    schema_format = schema.get("schema_format") or schema.get("format")
    if schema_format:
        result["format"] = schema_format

    if is_required and schema.get("nullable"):
        result["nullable"] = True

    required_set = set(schema.get("required", []))
    if required_set:
        result["required"] = sorted(required_set)

    if "properties" in schema:
        result["properties"] = {
            name: _normalize_schema(prop_schema, is_required=name in required_set)
            for name, prop_schema in sorted(schema["properties"].items())
        }

    if "items" in schema:
        result["items"] = _normalize_schema(schema["items"])

    if "enum" in schema:
        result["enum"] = sorted(schema["enum"]) if schema["enum"] else []

    if "additionalProperties" in schema:
        ap = schema["additionalProperties"]
        result["additionalProperties"] = _normalize_schema(ap) if isinstance(ap, dict) else ap

    return result


def _validate_spec_overrides(
    spec_overrides: SpecOverrides,
    consumed_overrides: set[tuple[str, str]],
    consumed_required_overrides: set[tuple[str, str]],
    spec_operation_ids: set[str],
) -> None:
    """Validate that all spec overrides reference valid operations and fields."""
    # Validate force_array_response
    for operation_id in spec_overrides.force_array_response:
        if operation_id not in spec_operation_ids:
            raise ValueError(
                f"force_array_response references unknown operation '{operation_id}'. "
                "Check that the operationId exists in the OpenAPI spec."
            )

    # Validate force_paginated
    for operation_id in spec_overrides.force_paginated:
        if operation_id not in spec_operation_ids:
            raise ValueError(
                f"force_paginated references unknown operation '{operation_id}'. "
                "Check that the operationId exists in the OpenAPI spec."
            )

    # Validate response field overrides
    for operation_id, fields in spec_overrides.response_fields.items():
        if operation_id not in spec_operation_ids:
            raise ValueError(
                f"Response field override references unknown operation '{operation_id}'. "
                "Check that the operationId exists in the OpenAPI spec."
            )

        for field_path in fields:
            if (operation_id, field_path) not in consumed_overrides:
                raise ValueError(
                    f"Response field override for '{operation_id}' field '{field_path}' was not applied. "
                    "Check that the field path exists in the response schema."
                )

    # Validate required field overrides
    for operation_id, fields in spec_overrides.required_fields.items():
        if operation_id not in spec_operation_ids:
            raise ValueError(
                f"Required field override references unknown operation '{operation_id}'. "
                "Check that the operationId exists in the OpenAPI spec."
            )

        for field_path in fields:
            if (operation_id, field_path) not in consumed_required_overrides:
                raise ValueError(
                    f"Required field override for '{operation_id}' field '{field_path}' was not applied. "
                    "Check that the field path exists in the response schema."
                )


def _write_schema_files(
    *,
    schemas: dict[str, str],
    schema_to_scope: dict[str, str],
    templates: Templates,
    output_dir: str,
) -> None:
    """Write per-module schema files and a main __init__.py that re-exports all."""
    schemas_by_scope: dict[str, dict[str, str]] = {}
    for class_name, class_def in schemas.items():
        scope = schema_to_scope[class_name]
        schemas_by_scope.setdefault(scope, {})[class_name] = class_def

    with open(f"{output_dir}/schemas/_base.py", "w") as f:
        f.write(templates.schema_base_template.render())

    all_exports: dict[str, list[str]] = {}
    for scope, scope_schemas in schemas_by_scope.items():
        module_name = to_snake_case(scope)
        sorted_schemas = sorted(scope_schemas.keys())
        all_exports[module_name] = sorted(sorted_schemas)

        schema_definitions = [scope_schemas[name] for name in sorted_schemas]
        with open(f"{output_dir}/schemas/_{module_name}.py", "w") as f:
            f.write(
                templates.schema_module_template.render(
                    scope=module_name,
                    schema_definitions=schema_definitions,
                )
            )

    sorted_exports = dict(sorted(all_exports.items()))
    all_schemas = sorted(name for names in all_exports.values() for name in names)
    with open(f"{output_dir}/schemas/__init__.py", "w") as f:
        f.write(
            templates.schema_init_template.render(
                exports=sorted_exports,
                all_schemas=all_schemas,
            )
        )
