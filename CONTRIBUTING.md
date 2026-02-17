# Contributing to CloudPulse

Thanks for your interest in contributing! This document describes how to get set up, make changes, and submit contributions.

## Ways to contribute
- Bug reports and reproduction cases
- Feature requests and design proposals
- Documentation improvements
- Code contributions (fixes, enhancements, tests)

## Development setup
- Required: Docker, Docker Compose, Node.js 18+, Python 3.11+

### Quick start (Docker)
```sh
# from repo root
docker compose up -d --build
# Frontend on http://localhost:3000, API on http://localhost:8000
```

### Local dev (hot reload)
- Backend: `uvicorn app.main:app --reload`
- Frontend: `cd frontend && npm install && npm run dev`

## Branching and commits
- Create feature branches from `main` (e.g., `feat/integrations-ui`)
- Write clear commit messages. If you use the DCO sign-off, append:
  `Signed-off-by: Your Name <you@example.com>`

## Tests and linting
- Please include tests where reasonable and run linters/formatters before submitting.

## Pull requests
- Include a clear description, screenshots for UI, and any migration notes
- Update docs/README if behavior or APIs change
- Ensure CI is green

## Licensing of contributions
By contributing, you agree that your contributions are licensed under the repository’s license (Business Source License 1.1) and, after the Change Date, under the stated Change License (Apache-2.0). See `LICENSE` and `CLA.md`.

## Code of Conduct
Participation in this project is governed by our `CODE_OF_CONDUCT.md`.