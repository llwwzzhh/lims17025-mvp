# Repository development

## Run the application

```bash
docker compose up --build
```

Web UI: http://localhost:5173  
API docs: http://localhost:8000/docs

The frontend is a React/TypeScript operational dashboard. Use `docker compose exec api python -m app.bootstrap_admin` to create the initial administrator, then sign in through the web UI.

## Checks

```bash
cd frontend && npm install && npm test && npm run build
cd ../backend && pip install -r requirements.txt && python -m compileall -q app
```

Current tests are a small initial smoke-test foundation. CI, backend integration tests, controlled database migrations, durable raw-file storage, report rendering, stronger production security configuration, and full intended-use validation are still required. Do not treat this development MVP as a validated production LIMS.
