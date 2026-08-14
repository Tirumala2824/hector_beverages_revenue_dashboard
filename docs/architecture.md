# Architecture and project structure

## Scope

This document records the repository boundaries and the locations that maintainers should inspect first. It is a baseline and should be refined as the project architecture becomes clearer.

## Top-level entries

- `.gitignore`
- `README.md`
- `data`
- `main.py`
- `requirements.txt`
- `static`
- `templates`

## Responsibilities

Document the main application, data, UI, integration, and persistence boundaries here. Keep external services and trust boundaries explicit.

## Data and dependency flow

Describe inputs, transformations, storage, outputs, background jobs, and external APIs. State where validation, authentication, authorization, retries, and error handling occur.

## Maintainability notes

Prefer small modules with explicit interfaces. Keep tests close to the behavior they protect and keep generated or local-only files out of version control.
