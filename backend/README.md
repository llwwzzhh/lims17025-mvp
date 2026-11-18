# FastAPI backend

## Run with Docker Compose

From the repository root:

```bash
docker compose up --build
```

API docs: http://localhost:8000/docs
Liveness: http://localhost:8000/health/live
Readiness: http://localhost:8000/health/ready

The API initializes MVP tables and standard roles on startup. Create the first admin interactively:

```bash
docker compose exec api python -m app.bootstrap_admin
```

Then use `POST /api/auth/token` with JSON `{"username":"...","password":"..."}`. Pass the returned bearer token to `/api/auth/me` and other protected endpoints. Admins can create accounts at `POST /api/users`; passwords must be at least 12 characters.

## Security and compliance notes

This is an early development foundation, not a validated production system. Set a unique, high-entropy `JWT_SECRET` outside source control before any non-local deployment. The MVP's automatic `create_all` is for development only; production requires reviewed schema migrations, security review, TLS, a secrets manager, backup/restore testing, operational monitoring, and laboratory validation. The audit table is application-level audit logging and is not tamper-proof against database administrators. Do not use this MVP as the sole authoritative record system until the laboratory has validated it for its intended use.
