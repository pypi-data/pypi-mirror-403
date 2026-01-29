# Plan: Implement pybumpit CLI with interactive prompts

**Status:** Completed
**Date:** 2026-01-25

## Goal

Create a CLI tool that mimics `npm version` behavior for Python projects, allowing users to bump versions in pyproject.toml with automatic git commit and tag creation.

## Summary of Changes

- Implemented version reading/writing from pyproject.toml using tomlkit (preserves formatting)
- Added version bumping logic for patch/minor/major
- Created interactive mode using python-clack for selecting version type
- Added CLI argument support for non-interactive usage
- Implemented dirty working directory check (fails if uncommitted changes exist)
- Added `--force` flag to override dirty check
- Git integration: automatic commit with `v{version}` message and annotated tag creation
- Works without git (just updates pyproject.toml)

## Files Modified

- [main.py](main.py) - Full CLI implementation with type annotations (~120 lines)
- [pyproject.toml](pyproject.toml) - Added dependencies (python-clack, tomlkit), dev tools (ruff, pyright), CLI entry point, and tool configurations
- [.gitignore](.gitignore) - Standard Python project ignores

## Breaking Changes

None (initial release)

## Deprecations

None
