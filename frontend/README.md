# Frontend

React + TypeScript + Vite web client for the LIMS MVP. Start the full stack from the repository root with `docker compose up --build`; open http://localhost:5173. API docs are available at http://localhost:8000/docs.

For local development, run `npm install && npm run dev` in this directory. Set `VITE_API_BASE` if the API is hosted on another origin. `npm test` runs the frontend unit tests and `npm run build` performs a TypeScript check and production build.

The current UI provides login, operational overview, lists for customers/contracts/samples/tasks/equipment/reports and quality records, plus creation forms for basic records. Workflow actions such as contract review, document approval, task execution/review, corrections, and report approval are currently available through the API Swagger UI; they are not yet exposed as UI controls. This is an early development MVP and must not be used for controlled laboratory records before full security, usability, integration, and intended-use validation.
