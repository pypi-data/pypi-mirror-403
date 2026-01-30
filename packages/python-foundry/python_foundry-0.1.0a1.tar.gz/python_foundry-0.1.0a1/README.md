# python-foundry Copier Template (Pre-Beta)

## WIP / NOT READY FOR USE

This project is a **work in progress**. It is published as a **pre-beta placeholder** primarily to reserve the name on PyPI.
Do **not** use it for real projects yet.

An opinionated Copier template for Python projects that bakes in a smooth dev loop: Make for common tasks, Ruff + MyPy for quality, Pytest for tests, Nox for automation, MkDocs for docs, and ready-to-use AI prompt helpers.

> Status: **pre-beta** — interfaces and defaults will change. Expect breaking updates until v0.1.0.
> Note: This PyPI package (`python-foundry`) does not provide a runtime Python module.

## Highlights

- **Copier-first** scaffolding with sensible defaults
- **uv** for fast, reproducible installs and builds
- **Ruff + MyPy** for fast linting and typing
- **Pytest** wired for speedy feedback
- **Nox** sessions to standardize local/CI runs
- **MkDocs** for documentation out of the box
- **Make** shortcuts for format, lint, test, docs, release
- **AI prompts** to guide common maintenance and release tasks

## Quick start (template consumers)

**Not available yet.**

This section will be filled in once the template is usable.

## Development (template maintainers)

- Run `make fmt` then `make lint` to keep code clean.
- Use `nox -s tests` for the canonical test suite.
- Build docs locally with `make docs-serve` (MkDocs live reload).
- When ready for a pre-release, update `pyproject.toml` metadata and `CHANGELOG.md`, then publish via `make release` (to be scripted).

## AI prompt helpers

A curated set of prompts will live under `docs/ai-prompts/` to speed up fixes, reviews, and releases. These will expand as the template matures.

## Status and support

This template is still stabilizing. Please open issues with clear repro steps and share your environment details.
