# Security Policy

## Supported versions

The `main` branch and current production deployment are supported for security fixes.

## Reporting a vulnerability

Please do not open public issues for sensitive vulnerabilities.

- Email: `support@skymodderai.com`
- Subject: `Security report - ModCheck`
- Include:
  - Steps to reproduce
  - Affected endpoint/page
  - Potential impact
  - Suggested fix (if available)

We will acknowledge reports as quickly as possible and coordinate disclosure once a fix is available.

## Security basics in this project

- Session cookies are `HttpOnly` and `SameSite=Lax`.
- Production responses include baseline security headers.
- Payment data is handled by Stripe (card details are not processed directly by this app).
- Secrets should be configured via environment variables and never committed.
- OpenClaw Lab (if enabled) is designed to run behind explicit acknowledgements and a dedicated sandbox workspace path.
