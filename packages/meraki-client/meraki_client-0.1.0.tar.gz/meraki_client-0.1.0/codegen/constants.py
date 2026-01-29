"""Shared constants for code generation."""

import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(SCRIPT_DIR, "templates")
SPEC_OVERRIDES_FILE = os.path.join(SCRIPT_DIR, "spec_overrides.toml")

# Python keywords and builtins that cannot be used as parameter names
RESERVED_NAMES = {
    "and",
    "as",
    "assert",
    "async",
    "await",
    "break",
    "class",
    "continue",
    "def",
    "del",
    "elif",
    "else",
    "except",
    "finally",
    "for",
    "from",
    "global",
    "if",
    "import",
    "in",
    "is",
    "lambda",
    "nonlocal",
    "not",
    "or",
    "pass",
    "raise",
    "return",
    "try",
    "while",
    "with",
    "yield",
    "type",
    "list",
    "dict",
    "set",
    "str",
    "int",
    "float",
    "bool",
    "object",
    "filter",
    "format",
    "hash",
    "input",
    "open",
    "range",
    "zip",
}
