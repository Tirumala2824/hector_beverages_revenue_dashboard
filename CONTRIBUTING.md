# Contributing

Thank you for considering a contribution. This repository uses a review-first workflow so that changes remain understandable, tested, and maintainable.

## Before opening a change

Read the README and the relevant documentation under `docs/`. For a bug, include a minimal reproduction, expected behavior, actual behavior, environment details, and relevant logs with secrets removed. For a feature, explain the user problem, proposed behavior, alternatives considered, and testing plan.

## Development workflow

Create a focused branch from the default branch using a descriptive name such as `feat/short-description`, `fix/short-description`, or `docs/short-description`. Keep commits small and meaningful. Do not commit credentials, local environment files, generated build output, private datasets, or dependency caches.

Before opening a pull request, run the documented installation, formatting, linting, type-checking, and test commands that apply to the project. Update documentation and the changelog when behavior or public interfaces change.

## Pull requests

Use the pull-request template. A pull request should explain the change, link the relevant issue, identify risks and migrations, include tests or a reason tests are not applicable, and include screenshots for visual changes. Maintainers may request revisions before merging.

## Code of conduct and security

Please follow [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md). Do not report security vulnerabilities in public issues; follow [`SECURITY.md`](SECURITY.md).
