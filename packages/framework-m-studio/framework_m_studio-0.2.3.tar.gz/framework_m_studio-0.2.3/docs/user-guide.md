# Studio User Guide

## Overview

Framework-M Studio is a visual development environment for creating and managing DocTypes.

## Starting Studio

```bash
# Start Studio server
uv run m studio

# Or with a specific port
uv run m studio --port 8000
```

Then open http://localhost:8000/studio in your browser.

## Creating a DocType

1. **Navigate to DocTypes** - Click "DocTypes" in the sidebar
2. **Click "Create"** - Opens the DocType editor
3. **Enter Name** - Use PascalCase (e.g., `SalesOrder`)
4. **Add Fields** - Click "Add Field" and configure each field
5. **Save** - Click "Save" to generate the Python file

## Adding Fields

Each field has:
- **Name** - Python identifier (snake_case)
- **Type** - Select from: Text, Integer, Float, Boolean, Date, etc.
- **Required** - Whether the field is mandatory
- **Default** - Optional default value
- **Validators** - Min/max length, pattern, min/max value

## Configuring Permissions

Permissions are defined in the DocType's Config class:
- Enable in the Properties panel
- Set `is_submittable = True` for workflow-enabled docs

## Using Git Mode

**Viewing Status:**
1. Click the Git icon in the sidebar
2. See current branch, modified files, and commit history

**Committing Changes:**
1. Make changes to DocTypes
2. Open Git panel
3. Enter commit message
4. Click "Commit"

**Pushing to Remote:**
1. Commit your changes first
2. Click "Push" to upload to GitHub

## Sandbox Mode

Test DocTypes without saving:
1. Open a DocType
2. Switch to "Sandbox" tab
3. Use auto-generated mock data
4. Test CRUD operations
5. Verify validation rules

## Controller Hooks

Available lifecycle hooks:
- `validate` - Before save validation
- `before_save` - Pre-persistence logic
- `after_save` - Post-save side effects
- `before_delete` - Pre-delete cleanup

Edit in the "Controller" tab.
