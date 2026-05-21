# AGENTS for Create_Locator_Service

This file is for AI coding agents working on the locator service project.

## Project overview

- Main entry point: `build_locator.py`
- Core framework: `core.py`
- Dataset definitions: `plugins/*.py`
- Helper modules: `utils/*.py`
- Additional dataset definitions are present in `pre_plugins/`, but the current `build_locator.py` only auto-discovers `plugins/`.

## What the agent should know

- The script builds ArcGIS geocoding locator services using `arcpy`.
- The main CLI options are:
  - `--all` to build all registered datasets and a composite locator
  - `--list` to show available dataset plugins
  - `--dataset NAME` to build a single dataset
  - `--fgdb-base PATH` required base path for the output file geodatabase
  - `--project-root PATH` optional project root directory
  - `--use-local-gdb` to materialize from a local file geodatabase instead of SDE
  - `--local_gdb PATH` path to the local FGDB when using `--use-local-gdb`

- Plugin registration pattern:
  - `core.py` defines `register_dataset(cfg)` and `discover_plugins(package, ctx)`
  - Each plugin must export `register(register_fn, ctx)`
  - Plugins call `register_fn(cfg)` with a `DatasetConfig`

- `DatasetConfig` handles:
  - data materialization from SDE or local FGDB
  - optional preprocessing and processing
  - field schema changes and row updates
  - locator creation via `locator_func`

## Agent behavior guidance

- Prefer changes in `plugins/` for dataset-specific behavior.
- Keep `core.py` focused on shared dataset orchestration and plugin discovery.
- Do not assume `pre_plugins/` is automatically loaded; it appears to be separate or legacy.
- Preserve existing ArcGIS/`arcpy` patterns and avoid refactoring into incompatible GIS libraries.

## Useful quick references

- `README.md` for command examples and plugin structure notes
- `build_locator.py` for CLI and main execution flow
- `core.py` for dataset lifecycle, context management, and plugin discovery

## Notes for future customization files

- A `.github/copilot-instructions.md` could be added later if repository-level workflow or policy guidance is needed.
- A custom skill might make sense for plugin authoring and `arcpy` field-mapping conventions.
