# Agent Instructions

## Code Generation

This project uses code generation to create Python SDK from the Meraki Dashboard OpenAPI specification.

After making changes to codegen templates or logic, regenerate the SDK:

```bash
make generate
```

## Verification

To verify changes, run linters and type checking (never run tests unprompted):

```bash
make lint
```
