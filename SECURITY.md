# Security Policy

## Supported versions

Security fixes are prioritized for the default branch and the most recent documented release, when releases are maintained. Older snapshots may not receive security updates.

## Reporting a vulnerability

Please do not disclose vulnerabilities in public issues. Report suspected vulnerabilities privately through the repository's GitHub security advisory or private contact channel, including a clear description, affected files or versions, reproduction steps, impact assessment, and a suggested mitigation where available.

Remove credentials and personal data from reports. Do not include live secrets. If a secret may have been exposed, revoke or rotate it immediately through the relevant provider and then report the incident.

## Security expectations

Dependencies should be kept current, input should be validated at trust boundaries, logs should not contain secrets, and production configuration should be supplied through a secret manager or deployment environment rather than committed files.
