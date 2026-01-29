"""Code generation package for Framework M Studio.

This package provides:
- LibCST-based parsing for existing DocType files
- Jinja2-based code generation for new files
- Transformers for modifying existing files while preserving formatting
- Test generators for DocTypes
"""

from framework_m_studio.codegen.generator import (
    generate_doctype_source,
    update_doctype_source,
)
from framework_m_studio.codegen.parser import (
    ConfigSchema,
    DocTypeSchema,
    FieldSchema,
    parse_doctype,
)
from framework_m_studio.codegen.test_generator import (
    generate_test,
    generate_test_file,
)

__all__ = [
    "ConfigSchema",
    "DocTypeSchema",
    "FieldSchema",
    "generate_doctype_source",
    "generate_test",
    "generate_test_file",
    "parse_doctype",
    "update_doctype_source",
]
