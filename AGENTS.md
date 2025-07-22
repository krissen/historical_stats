# AGENTS.md

## Project Purpose

This project is a Home Assistant custom integration that provides flexible, configurable historical statistics for any entity. It exposes user-defined measurement points (such as “max last 7 days” or “value 24h ago”) as attributes on a sensor entity, using efficient and DRY principles.

## Automated Agent Instructions

### Directory and File Handling

- In the `custom_components/historical_stats/translations/` directory, only process the `en.json` file. All other files in this directory must be ignored.

### Coding Principles

- All code must follow the KISS (Keep It Simple, Stupid) and DRY (Don't Repeat Yourself) principles.

### Comments and Documentation

- All code should be commented for clarity.
- All documentation, including comments, must be written in English.
