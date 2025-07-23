# AGENTS.md

## Project Purpose

This project is a Home Assistant custom integration that provides flexible, configurable historical statistics for any entity. It exposes user-defined measurement points (such as “max last 7 days” or “value 24h ago”) as attributes on a sensor entity, using efficient and DRY principles.

## Automated Agent Instructions

### Directory and File Handling

- In the `custom_components/historical_stats/translations/` directory, only process the `en.json` file. All other files in this directory must be ignored.

### Coding Principles

- All code must follow the KISS (Keep It Simple, Stupid) and DRY (Don't Repeat Yourself) principles.
- If the task at hand involves several distinct steps, said steps must be added to the codebase in separate commits.
- Code must be aligned with the latest documentation and guidelines of the Home Assistant project.
- Commit messages must be clear and descriptive, following the format: `feat: <description>` for new features, `fix: <description>` for bug fixes, and `docs: <description>` for documentation changes.

### Comments and Documentation

- All code must be commented for clarity.
- All documentation, including comments, must be written in English.
