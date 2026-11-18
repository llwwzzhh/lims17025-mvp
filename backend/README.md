# LIMS MVP backend — development status

Run from the repository root:

```bash
docker compose up --build
```

OpenAPI: http://localhost:8000/docs

Create an administrator using `docker compose exec api python -m app.bootstrap_admin`, obtain a token from `POST /api/auth/token`, then authorize in Swagger with `Bearer <token>`.

## API groups currently available

- Identity: `/api/auth/*`, `/api/users`
- Customers/contracts: `/api/customers`, `/api/contracts`
- Samples and custody events: `/api/samples`
- Controlled documents and versions: `/api/documents`
- Equipment: `/api/equipment`
- Test templates/tasks: `/api/test-templates`, `/api/tasks`
- Raw data and correction history: `/api/raw-data`
- Technical reviews and reports: `/api/tasks/{id}/reviews`, `/api/reports`
- Nonconformities: `/api/nonconformities`
- System validation records: `/api/system-validations`
- Audit query: `/api/audit-logs`

Raw measurement records are retained as submitted. Corrections are stored as separate records with the previous values and reason; the API does not overwrite the original record. Approved reports are revised by creating a new version. Audit rows are application-level records and are not tamper-proof against database administrators.

## Known limitations

This is a development MVP, not production-ready or validated software. The current schema bootstrap uses SQLAlchemy `create_all`; reviewed database migrations, automated tests, security hardening, durable raw-file storage, report rendering/signatures, backup/restore procedures, and complete approval workflows remain necessary. The first release must be validated for the laboratory's intended use before it is relied on for controlled records. A backup endpoint is intentionally not exposed through the application; database backups should be performed by an authorized infrastructure operator with protected storage and restoration tests.
