# MedEase — Round 2 (Vercel Ready)

## Round 2 pivot

Problem statement: a 90-day global emergency has been declared and people cannot gather in person.
MedEase becomes the **remote recovery verification layer** that lets a hospital discharge a patient
early (freeing a bed for surge capacity) while still proving — to the hospital, an insurer, and the
patient's family — that recovery is on track, without anyone needing to meet in person.

This version adds a full, demonstrable **monetization layer** on top of the Round 1 access/cost/state
architecture:

- **Multi-patient backend** — 4 seeded patients across 2 hospitals, so the product can show an
  aggregate, hospital-facing view instead of a single demo patient.
- **`/api/business/overview`** — live revenue math across three streams (hospital subscription,
  insurer data license, pharmacy commission), plus bed-days-freed and flagged-patient signals.
- **`/api/pharmacy/reorder`** — a simulated contactless pharmacy reorder that earns a real commission
  in the running ledger.
- **`/api/pricing`** — the full 5-tier pricing model (see below), served as data so it's provable, not
  just a slide claim.
- **New "Business" tab in the app** — patients and judges can see the live revenue simulator, pricing
  tiers, and pandemic-impact snapshot without leaving the product.
- **Pandemic banner** — "Emergency Day 42/90 · No in-person gathering" is shown persistently across
  every screen to keep Round 2's constraint visible throughout the demo.

## Structure

- `public/index.html` — MedEase frontend (extends the Round 1 UI with a Business tab, pandemic
  banner, and a pharmacy-reorder action on the checklist)
- `api/index.py` — Flask REST API (multi-patient + monetization endpoints)
- `requirements.txt` — Python dependency
- `vercel.json` — Vercel routing/build configuration

## Deploy

1. Upload this folder to GitHub.
2. In Vercel, choose **Add New → Project**.
3. Import the GitHub repository.
4. Click **Deploy**. No environment variables are required for this demo.

## API endpoints

- `GET /api/health`
- `GET /api/emergency` — the Round 2 scenario (day count, no-gathering rule)
- `GET /api/patients/<id>` — `MED-1042`, `MED-2091`, `MED-3087`, `MED-4415`
- `GET /api/events?patient_id=<id>`
- `POST /api/events`
- `GET /api/recovery-state/<id>`
- `GET /api/budget`
- `GET /api/pricing` — the 5-tier monetization model
- `GET /api/business/overview` — live aggregate + revenue dashboard data
- `POST /api/pharmacy/reorder` — simulate a commission-earning pharmacy reorder

## Monetization model

| Tier | Who pays | Model | Rate |
|---|---|---|---|
| Patient App | Patients & families | Free, forever | ₹0 |
| Hospital Pro | Hospitals | Per-discharge SaaS subscription | ₹49 / patient / month |
| Insurer / TPA Data License | Insurers & TPAs | Per verified adherence event | ₹5 / event |
| Pharmacy Partner Network | Partner pharmacies | Affiliate commission | ₹18 / reorder |
| Public Health / Gov License | State health departments | Flat emergency-response contract | ₹8L / region / 90-day emergency |

## Important

The backend currently uses an in-memory event store so it can be deployed immediately without
database credentials. Vercel serverless instances are not a durable database; for a production
version, replace `EVENTS`, `PATIENTS`, and `PHARMACY_LEDGER` with Supabase/Postgres.

For the hackathon demo, this gives you a real frontend → REST API → backend flow, with a live,
provable monetization layer, while preserving the existing Round 1 prototype and its four
resilience challenges.
