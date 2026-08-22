from flask import Flask, jsonify, request, send_from_directory
from datetime import datetime, timezone
from pathlib import Path
import os

app = Flask(__name__, static_folder="../public", static_url_path="")

# Demo data. Replace the in-memory store with Supabase/Postgres for production persistence.
PATIENT = {
    "id": "MED-1042",
    "name": "R. Kapoor",
    "procedure": "Post-Appendectomy Discharge",
    "checklist": [
        {"type":"med", "en":{"title":"Take 1 tablet (Amoxicillin) after breakfast & dinner","sub":"For 5 days — do not skip a dose"},
         "hi":{"title":"नाश्ते और रात के खाने के बाद 1 गोली (एमॉक्सिसिलिन) लें","sub":"5 दिनों तक — कोई खुराक न छोड़ें"}},
        {"type":"do", "en":{"title":"Light walking is encouraged from Day 2","sub":"Helps circulation and healing"},
         "hi":{"title":"दूसरे दिन से हल्की सैर करें","sub":"रक्त संचार और घाव भरने में मदद करता है"}},
        {"type":"dont", "en":{"title":"No heavy lifting or driving for 14 days","sub":"Avoid strain on the incision"},
         "hi":{"title":"14 दिनों तक भारी सामान न उठाएं और गाड़ी न चलाएं","sub":"टांकों पर दबाव न डालें"}},
        {"type":"care", "en":{"title":"Change the dressing every morning","sub":"Keep the area clean and dry"},
         "hi":{"title":"हर सुबह ड्रेसिंग बदलें","sub":"घाव को साफ़ और सूखा रखें"}},
        {"type":"appt", "en":{"title":"Follow-up visit: Tue, 10:00 AM — Dr. Mehta","sub":"Bring this checklist with you"},
         "hi":{"title":"अगली मुलाक़ात: मंगलवार, सुबह 10:00 बजे — डॉ. मेहता","sub":"यह चेकलिस्ट साथ लाएं"}},
        {"type":"flag", "en":{"title":"Call the hospital if fever exceeds 101°F","sub":"Or if there is unusual swelling / discharge"},
         "hi":{"title":"अगर बुखार 101°F से ज़्यादा हो तो अस्पताल को कॉल करें","sub":"या असामान्य सूजन/स्राव होने पर"}},
    ]
}

EVENTS = []
BUDGET = {"limit": 1500, "used": 420, "calls": 7, "local": 91}

@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

@app.get("/api/health")
def health():
    return jsonify({"ok": True, "service": "MedEase API", "timestamp": datetime.now(timezone.utc).isoformat()})

@app.get("/api/patients/<patient_id>")
def get_patient(patient_id):
    if patient_id != PATIENT["id"]:
        return jsonify({"error": "Patient not found"}), 404
    return jsonify(PATIENT)

@app.get("/api/events")
def get_events():
    patient_id = request.args.get("patient_id", PATIENT["id"])
    return jsonify([e for e in EVENTS if e["patient_id"] == patient_id])

@app.post("/api/events")
def create_event():
    data = request.get_json(silent=True) or {}
    patient_id = data.get("patient_id", PATIENT["id"])
    if patient_id != PATIENT["id"]:
        return jsonify({"error": "Patient not found"}), 404
    if not data.get("method"):
        return jsonify({"error": "method is required"}), 400

    event = {
        "id": len(EVENTS) + 1,
        "patient_id": patient_id,
        "method": data["method"],
        "location": data.get("location", "Home"),
        "event_type": data.get("event_type", ""),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    EVENTS.insert(0, event)

    # Demo budget accounting: only paid/AI-like events increment spend.
    if "ai" in event["event_type"] or "ocr" in event["event_type"]:
        BUDGET["calls"] += 1
        BUDGET["used"] += 60

    return jsonify(event), 201

@app.get("/api/recovery-state/<patient_id>")
def recovery_state(patient_id):
    if patient_id != PATIENT["id"]:
        return jsonify({"error": "Patient not found"}), 404

    patient_events = [e for e in EVENTS if e["patient_id"] == patient_id]
    med = sum(e["method"] == "Medication taken" for e in patient_events)
    walk = sum(e["method"] == "Walking completed" for e in patient_events)
    hydration = sum(e["method"] == "Hydration completed" for e in patient_events)

    med_done = min(2, med)
    walk_done = min(4, walk)
    hydration_done = min(6, hydration)
    total = med_done + walk_done + hydration_done
    adherence = round(total / 12 * 100)

    return jsonify({
        "patient_id": patient_id,
        "medication_completed": med_done,
        "walking_completed": walk_done,
        "hydration_completed": hydration_done,
        "adherence": adherence,
        "status": "ON TRACK" if adherence >= 70 else "NEEDS ATTENTION",
        "last_verified": patient_events[0]["timestamp"] if patient_events else None
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
        "mode": mode
    })

# Local development only. Vercel imports the Flask app above.
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
