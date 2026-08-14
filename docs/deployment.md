# Deployment and production usage

## Current status

This repository was detected as **Python**. Confirm the target hosting platform, supported runtime, build command, start command, and required environment variables before production use.

## Deployment checklist

1. Pin the supported runtime and dependency versions.
2. Configure secrets through the deployment provider or GitHub environments; do not commit them.
3. Run migrations or initialization steps explicitly and back up data before changes.
4. Run tests and a smoke test against a non-production environment.
5. Configure logs, health checks, monitoring, and an owner for incidents.
6. Document rollback steps and the last known good release.

## Production configuration

Document required environment variables, databases, queues, storage, third-party services, domains, CORS, authentication, rate limits, and data-retention requirements here.
