from flask import Flask, jsonify, request, send_from_directory
from datetime import datetime, timezone, timedelta
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent
PUBLIC_DIR = BASE_DIR / "public"

app = Flask(
    __name__,
    static_folder=str(PUBLIC_DIR),
    static_url_path=""
)

# ---------------------------------------------------------------------------
# ROUND 2 CONTEXT
# A 90-day no-gathering emergency has been declared. Hospitals must discharge
# patients earlier to free beds for the surge, but in-person follow-ups are
# banned. MedEase becomes the remote verification layer that lets a hospital
# discharge safely, an insurer trust the adherence signal, and a pharmacy
# re-engage the patient — all without anyone gathering in person.
# ---------------------------------------------------------------------------

EMERGENCY = {
    "declared": True,
    "day": 42,
    "total_days": 90,
    "rule": "No in-person gathering, including routine follow-up visits",
}

# Demo data. Replace the in-memory store with Supabase/Postgres for production persistence.
PATIENTS = {
    "MED-1042": {
        "id": "MED-1042",
        "name": "R. Kapoor",
        "procedure": "Post-Appendectomy Discharge",
        "hospital": "City Care Hospital",
        "plan": "hospital_pro",
        "checklist": [
            {"type":"med", "en":{"title":"Take 1 tablet (Amoxicillin) after breakfast & dinner","sub":"For 5 days — do not skip a dose"},
             "hi":{"title":"नाश्ते और रात के खाने के बाद 1 गोली (एमॉक्सिसिलिन) लें","sub":"5 दिनों तक — कोई खुराक न छोड़ें"}},
            {"type":"do", "en":{"title":"Light walking is encouraged from Day 2","sub":"Helps circulation and healing"},
             "hi":{"title":"दूसरे दिन से हल्की सैर करें","sub":"रक्त संचार और घाव भरने में मदद करता है"}},
            {"type":"dont", "en":{"title":"No heavy lifting or driving for 14 days","sub":"Avoid strain on the incision"},
             "hi":{"title":"14 दिनों तक भारी सामान न उठाएं और गाड़ी न चलाएं","sub":"टांकों पर दबाव न डालें"}},
            {"type":"care", "en":{"title":"Change the dressing every morning","sub":"Keep the area clean and dry"},
             "hi":{"title":"हर सुबह ड्रेसिंग बदलें","sub":"घाव को साफ़ और सूखा रखें"}},
            {"type":"appt", "en":{"title":"Remote follow-up: Tue, 10:00 AM — video call with Dr. Mehta","sub":"No in-person visit needed during the emergency"},
             "hi":{"title":"अगली मुलाक़ात: मंगलवार, सुबह 10:00 बजे — डॉ. मेहता से वीडियो कॉल","sub":"आपातकाल के दौरान अस्पताल आने की ज़रूरत नहीं"}},
            {"type":"flag", "en":{"title":"Call the hospital if fever exceeds 101°F","sub":"Or if there is unusual swelling / discharge"},
             "hi":{"title":"अगर बुखार 101°F से ज़्यादा हो तो अस्पताल को कॉल करें","sub":"या असामान्य सूजन/स्राव होने पर"}},
        ],
    },
    "MED-2091": {
        "id": "MED-2091",
        "name": "A. Sheikh",
        "procedure": "Post-Cardiac Stent Discharge",
        "hospital": "City Care Hospital",
        "plan": "hospital_pro",
        "checklist": [
            {"type":"med", "en":{"title":"Take Aspirin + Clopidogrel every morning","sub":"Do not stop without doctor's advice"}, "hi":{"title":"हर सुबह Aspirin + Clopidogrel लें","sub":"डॉक्टर की सलाह के बिना बंद न करें"}},
            {"type":"do", "en":{"title":"10-minute walk, twice a day","sub":"Build up slowly over the week"}, "hi":{"title":"दिन में दो बार 10 मिनट टहलें","sub":"हफ्ते भर में धीरे-धीरे बढ़ाएं"}},
            {"type":"dont", "en":{"title":"Avoid salt-heavy food for 30 days","sub":"Keeps blood pressure stable"}, "hi":{"title":"30 दिनों तक अधिक नमक वाला भोजन न करें","sub":"रक्तचाप स्थिर रखता है"}},
            {"type":"flag", "en":{"title":"Call immediately for chest pain or breathlessness","sub":"Do not wait for the next check-in"}, "hi":{"title":"सीने में दर्द या सांस फूलने पर तुरंत कॉल करें","sub":"अगली जांच का इंतज़ार न करें"}},
        ],
    },
    "MED-3087": {
        "id": "MED-3087",
        "name": "P. Iyer",
        "procedure": "Maternity Discharge — Normal Delivery",
        "hospital": "Sunrise Women's Hospital",
        "plan": "hospital_pro",
        "checklist": [
            {"type":"care", "en":{"title":"Keep the stitch area clean and dry","sub":"Change pads every 4-6 hours"}, "hi":{"title":"टांके वाली जगह को साफ़ और सूखा रखें","sub":"हर 4-6 घंटे में पैड बदलें"}},
            {"type":"do", "en":{"title":"Feed on demand, every 2-3 hours","sub":"Track feeds in the app"}, "hi":{"title":"हर 2-3 घंटे में स्तनपान कराएं","sub":"ऐप में फीड दर्ज करें"}},
            {"type":"flag", "en":{"title":"Call if bleeding increases or fever appears","sub":"Remote triage nurse is on call 24/7"}, "hi":{"title":"रक्तस्राव बढ़े या बुखार आए तो कॉल करें","sub":"रिमोट ट्राइएज नर्स 24/7 उपलब्ध"}},
        ],
    },
    "MED-4415": {
        "id": "MED-4415",
        "name": "S. Verma",
        "procedure": "COPD Exacerbation Discharge",
        "hospital": "Sunrise Women's Hospital",
        "plan": "hospital_pro",
        "checklist": [
            {"type":"med", "en":{"title":"Use inhaler as prescribed, twice daily","sub":"Rinse mouth after steroid inhaler"}, "hi":{"title":"निर्धारित अनुसार दिन में दो बार इनहेलर लें","sub":"स्टेरॉयड इनहेलर के बाद मुंह धोएं"}},
            {"type":"flag", "en":{"title":"Call if oxygen level drops below 92%","sub":"Use the home pulse oximeter provided at discharge"}, "hi":{"title":"ऑक्सीजन स्तर 92% से नीचे जाए तो कॉल करें","sub":"डिस्चार्ज पर दिया गया पल्स ऑक्सीमीटर उपयोग करें"}},
        ],
    },
}
DEFAULT_PATIENT_ID = "MED-1042"

# Seed a bit of history so the aggregate / revenue views aren't empty on first load.
def _seed_events():
    now = datetime.now(timezone.utc)
    seed = []
    seed_plan = [
        ("MED-1042", "Medication taken", "Home", 2),
        ("MED-1042", "Walking completed", "Home", 4),
        ("MED-1042", "Hydration completed", "Home", 3),
        ("MED-2091", "Medication taken", "Home", 2),
        ("MED-2091", "Walking completed", "Home", 2),
        ("MED-2091", "Hydration completed", "Home", 2),
        ("MED-3087", "Medication taken", "Home", 2),
        ("MED-3087", "Walking completed", "Home", 4),
        ("MED-3087", "Hydration completed", "Home", 6),
        ("MED-4415", "Medication taken", "Home", 2),
        ("MED-4415", "Walking completed", "Home", 1),
    ]
    i = 0
    for patient_id, method, location, count in seed_plan:
        for c in range(count):
            i += 1
            seed.append({
                "id": i,
                "patient_id": patient_id,
                "method": method,
                "location": location,
                "event_type": method.lower().replace(" ", "_"),
                "timestamp": (now - timedelta(hours=i * 3)).isoformat(),
            })
    return list(reversed(seed))

EVENTS = _seed_events()
NEXT_EVENT_ID = len(EVENTS) + 1

BUDGET = {"limit": 1500, "used": 420, "calls": 7, "local": 91}

# ---------------------------------------------------------------------------
# MONETIZATION MODEL (Round 2)
# Every number here is also surfaced in the product UI — the business model
# is demonstrable, not just a slide claim.
# ---------------------------------------------------------------------------
PRICING = {
    "patient_app": {
        "label": "Patient App",
        "who": "Patients & families",
        "model": "Free, forever",
        "rate": "₹0",
        "why": "Free access drives adoption and generates the verified adherence data every other tier is priced on.",
    },
    "hospital_pro": {
        "label": "Hospital Pro",
        "who": "Hospitals & discharge wards",
        "model": "Per-discharge SaaS subscription",
        "rate": "₹49 / patient / month",
        "why": "Cheaper than the ₹15,000-₹44,000 an avoidable readmission costs — hospitals save far more than they pay.",
    },
    "insurer_license": {
        "label": "Insurer / TPA Data License",
        "who": "Insurers & third-party administrators",
        "model": "Per verified adherence record",
        "rate": "₹5 / verified event",
        "why": "A timestamped, tamper-evident adherence trail is a better underwriting signal than a self-reported claim.",
    },
    "pharmacy_commission": {
        "label": "Pharmacy Partner Network",
        "who": "Partner pharmacies",
        "model": "Affiliate commission per fulfilled reorder",
        "rate": "₹18 / reorder",
        "why": "The checklist is a natural, contactless re-engagement point for refills during a no-gathering period.",
    },
    "gov_license": {
        "label": "Public Health / Government License",
        "who": "State health departments",
        "model": "Flat emergency-response contract",
        "rate": "₹8L / region / 90-day emergency",
        "why": "One aggregated, anonymized compliance dashboard across every partnered hospital in the region.",
    },
}

PHARMACY_COMMISSION_RATE = 18  # INR per fulfilled reorder
INSURER_RATE = 5               # INR per verified event supplied to an insurer
HOSPITAL_RATE_PER_PATIENT = 49 # INR per patient per month
BED_DAYS_SAVED_PER_PATIENT = 2.4  # illustrative: early-but-safe discharge vs. holding a bed for observation

PHARMACY_LEDGER = {"reorders": 3, "commission_earned": 3 * PHARMACY_COMMISSION_RATE}


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/api/health")
def health():
    return jsonify({"ok": True, "service": "MedEase API", "timestamp": datetime.now(timezone.utc).isoformat()})


@app.get("/api/emergency")
def emergency():
    return jsonify(EMERGENCY)


@app.get("/api/patients/<patient_id>")
def get_patient(patient_id):
    patient = PATIENTS.get(patient_id)
    if not patient:
        return jsonify({"error": "Patient not found"}), 404
    return jsonify(patient)


@app.get("/api/events")
def get_events():
    patient_id = request.args.get("patient_id", DEFAULT_PATIENT_ID)
    return jsonify([e for e in EVENTS if e["patient_id"] == patient_id])


@app.post("/api/events")
def create_event():
    global NEXT_EVENT_ID
    data = request.get_json(silent=True) or {}
    patient_id = data.get("patient_id", DEFAULT_PATIENT_ID)
    if patient_id not in PATIENTS:
        return jsonify({"error": "Patient not found"}), 404
    if not data.get("method"):
        return jsonify({"error": "method is required"}), 400

    event = {
        "id": NEXT_EVENT_ID,
        "patient_id": patient_id,
        "method": data["method"],
        "location": data.get("location", "Home"),
        "event_type": data.get("event_type", ""),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    NEXT_EVENT_ID += 1
    EVENTS.insert(0, event)

    # Demo budget accounting: only paid/AI-like events increment spend.
    if "ai" in event["event_type"] or "ocr" in event["event_type"]:
        BUDGET["calls"] += 1
        BUDGET["used"] += 60

    return jsonify(event), 201


def _adherence_for(patient_id):
    patient_events = [e for e in EVENTS if e["patient_id"] == patient_id]
    med = sum(e["method"] == "Medication taken" for e in patient_events)
    walk = sum(e["method"] == "Walking completed" for e in patient_events)
    hydration = sum(e["method"] == "Hydration completed" for e in patient_events)
    med_done = min(2, med)
    walk_done = min(4, walk)
    hydration_done = min(6, hydration)
    total = med_done + walk_done + hydration_done
    adherence = round(total / 12 * 100) if total else 0
    return adherence, patient_events


@app.get("/api/recovery-state/<patient_id>")
def recovery_state(patient_id):
    if patient_id not in PATIENTS:
        return jsonify({"error": "Patient not found"}), 404

    adherence, patient_events = _adherence_for(patient_id)
    med = sum(e["method"] == "Medication taken" for e in patient_events)
    walk = sum(e["method"] == "Walking completed" for e in patient_events)
    hydration = sum(e["method"] == "Hydration completed" for e in patient_events)

    return jsonify({
        "patient_id": patient_id,
        "medication_completed": min(2, med),
        "walking_completed": min(4, walk),
        "hydration_completed": min(6, hydration),
        "adherence": adherence,
        "status": "ON TRACK" if adherence >= 70 else "NEEDS ATTENTION",
        "last_verified": patient_events[0]["timestamp"] if patient_events else None,
    })


@app.get("/api/budget")
def budget():
    used = BUDGET["used"]
    limit = BUDGET["limit"]
    ratio = used / limit
    mode = "PROTECTED" if ratio >= 1 else ("OPTIMIZED" if ratio >= .7 else "NORMAL")
    return jsonify({
        **BUDGET,
        "remaining": max(0, limit - used),
        "mode": mode,
    })


# ---------------------------------------------------------------------------
# ROUND 2 — MONETIZATION + PANDEMIC-SCALE ENDPOINTS
# ---------------------------------------------------------------------------

@app.get("/api/pricing")
def pricing():
    return jsonify(PRICING)


@app.get("/api/business/overview")
def business_overview():
    """Aggregate, hospital-facing view: this is the paid product."""
    patient_ids = list(PATIENTS.keys())
    adherences = []
    flagged = []
    for pid in patient_ids:
        a, _ = _adherence_for(pid)
        adherences.append(a)
        if a < 70:
            flagged.append(pid)

    patients_monitored = len(patient_ids)
    avg_adherence = round(sum(adherences) / len(adherences)) if adherences else 0
    bed_days_freed = round(patients_monitored * BED_DAYS_SAVED_PER_PATIENT, 1)
    verified_events = len(EVENTS)

    hospital_revenue = patients_monitored * HOSPITAL_RATE_PER_PATIENT
    insurer_revenue = verified_events * INSURER_RATE
    pharmacy_revenue = PHARMACY_LEDGER["commission_earned"]
    total_revenue = hospital_revenue + insurer_revenue + pharmacy_revenue

    return jsonify({
        "emergency": EMERGENCY,
        "patients_monitored": patients_monitored,
        "avg_adherence": avg_adherence,
        "flagged_patients": flagged,
        "bed_days_freed": bed_days_freed,
        "verified_events": verified_events,
        "revenue": {
            "hospital_subscription": hospital_revenue,
            "insurer_license": insurer_revenue,
            "pharmacy_commission": pharmacy_revenue,
            "total_this_month": total_revenue,
        },
        "pharmacy_ledger": PHARMACY_LEDGER,
        "rates": {
            "hospital_per_patient": HOSPITAL_RATE_PER_PATIENT,
            "insurer_per_event": INSURER_RATE,
            "pharmacy_per_reorder": PHARMACY_COMMISSION_RATE,
        },
    })


@app.post("/api/pharmacy/reorder")
def pharmacy_reorder():
    """Simulates a patient re-ordering medicine through a partner pharmacy —
    a real, contactless transaction MedEase can take a commission on."""
    data = request.get_json(silent=True) or {}
    patient_id = data.get("patient_id", DEFAULT_PATIENT_ID)
    if patient_id not in PATIENTS:
        return jsonify({"error": "Patient not found"}), 404

    PHARMACY_LEDGER["reorders"] += 1
    PHARMACY_LEDGER["commission_earned"] += PHARMACY_COMMISSION_RATE

    global NEXT_EVENT_ID
    event = {
        "id": NEXT_EVENT_ID,
        "patient_id": patient_id,
        "method": "Pharmacy reorder",
        "location": "Pharmacy",
        "event_type": "pharmacy_reorder",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    NEXT_EVENT_ID += 1
    EVENTS.insert(0, event)

    return jsonify({
        "event": event,
        "pharmacy_ledger": PHARMACY_LEDGER,
        "commission_this_order": PHARMACY_COMMISSION_RATE,
    }), 201


# Local development only. Vercel imports the Flask app above.
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
