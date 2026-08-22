# MedEase — Vercel Ready

## Structure

- `public/index.html` — MedEase frontend (your existing UI)
- `api/index.py` — Flask REST API
- `requirements.txt` — Python dependency
- `vercel.json` — Vercel routing/build configuration

## Deploy

1. Upload this folder to GitHub.
2. In Vercel, choose **Add New → Project**.
3. Import the GitHub repository.
4. Click **Deploy**. No environment variables are required for this demo.

## API endpoints

- `GET /api/health`
- `GET /api/patients/MED-1042`
- `GET /api/events?patient_id=MED-1042`
- `POST /api/events`
- `GET /api/recovery-state/MED-1042`
- `GET /api/budget`

## Important

The backend currently uses an in-memory event store so it can be deployed immediately without database credentials. Vercel serverless instances are not a durable database; for a production version, replace `EVENTS` with Supabase/Postgres.

For the hackathon demo, this gives you a real frontend → REST API → backend flow while preserving the existing visual prototype.
