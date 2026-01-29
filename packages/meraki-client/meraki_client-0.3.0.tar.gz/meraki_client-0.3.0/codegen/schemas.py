"""Schemas for code generation."""

import pydantic


class BatchableAction(pydantic.BaseModel):
    """Custom OpenAPI extension for batchable actions."""

    group: str
    summary: str
    resource: str
    operation: str
