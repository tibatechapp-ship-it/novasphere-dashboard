# Security Policy

## Reporting a Vulnerability
Email: security@example.com (replace before publishing).

## Threat model
- Assets: JWT secret, DB credentials, Redis password, user data.
- Trust boundaries: Browser <-> Raqib (HTTPS, JWT cookie).
- Raqib never executes shell commands, eval, or exec.
- Runbooks are read-only guidance (ADR 0001).

## Baseline controls
- Passwords: bcrypt cost=12.
- JWT: HS256, expiry 24h, HttpOnly Secure SameSite=Strict in prod.
- Rate limits: login 10/min/IP, signup 5/min/IP, insights 30/min/user.
- CORS: explicit allow-list, no wildcard with credentials.
