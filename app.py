# app.py
from datetime import datetime, timezone
import hashlib

from flask import Flask, request, jsonify
from flask_cors import CORS
from pydantic import ValidationError

from models import SurveySubmission, StoredSurveyRecord
from storage import append_json_line

app = Flask(__name__)
CORS(app, resources={r"/v1/*": {"origins": "*"}})

def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({
        "status": "ok",
        "message": "API is alive",
        "utc_time": datetime.now(timezone.utc).isoformat()
    })

@app.post("/v1/survey")
def submit_survey():
    payload = request.get_json(silent=True)
    if payload is None:
        return jsonify({"error": "invalid_json", "detail": "Body must be application/json"}), 400

    try:
        submission = SurveySubmission(**payload)
    except ValidationError as ve:
        return jsonify({"error": "validation_error", "detail": ve.errors()}), 422

    # ---------- NEW: derive/normalize values ----------
    # Normalize email before hashing / submission_id
    email_norm = submission.email.strip().lower()

    # Hash PII (store ONLY hashes in the saved record)
    email_sha = sha256_hex(email_norm)
    age_sha   = sha256_hex(str(submission.age))

    # submission_id: use provided, else sha256(email + YYYYMMDDHH) in UTC
    sub_id = submission.submission_id
    if not sub_id:
        hour_stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H")
        sub_id = sha256_hex(email_norm + hour_stamp)

    # user_agent: prefer payload value; else read from headers
    user_agent = submission.user_agent or request.headers.get("User-Agent")

    # ---------- Build stored record (NO raw email/age) ----------
    record = StoredSurveyRecord(
        submission_id=sub_id,
        name=submission.name,
        email_sha256=email_sha,
        age_sha256=age_sha,
        consent=submission.consent,
        rating=submission.rating,
        comments=submission.comments,
        source=submission.source or "other",
        user_agent=user_agent,
        received_at=datetime.now(timezone.utc),
        ip=request.headers.get("X-Forwarded-For", request.remote_addr or "")
    )

    append_json_line(record.dict())
    return jsonify({"status": "ok", "submission_id": sub_id}), 201


if __name__ == "__main__":
    # Bind to all interfaces + stable port for your proxy
    app.run(host="0.0.0.0", port=41845, debug=True)