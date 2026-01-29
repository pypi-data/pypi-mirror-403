# Framework M Studio

Visual DocType builder and developer tools for Framework M.

[![PyPI version](https://badge.fury.io/py/framework-m-studio.svg)](https://badge.fury.io/py/framework-m-studio)
[![GitLab Pipeline Status](https://gitlab.com/castlecraft/framework-m/badges/main/pipeline.svg)](https://gitlab.com/castlecraft/framework-m/-/pipelines)

## Overview

`framework-m-studio` provides development-time tools that are NOT included in the production runtime:

- **Studio UI**: Visual DocType builder (React + Vite)
- **Code Generators**: LibCST-based Python code generation
- **DevTools CLI**: `m codegen`, `m docs:generate`

> **Note:** Studio is for developers to build DocTypes. The **Desk** (end-user data management UI) is a separate frontend that connects to the Framework M backend.

## Installation

```bash
# Add to your project's dev dependencies
uv add --dev framework-m-studio
```

## Usage

```bash
# Start Studio UI
m studio

# Generate TypeScript client from OpenAPI
m codegen client --lang ts --out ./frontend/src/api
```

## Development

```bash
cd apps/studio
uv sync
uv run pytest
```
