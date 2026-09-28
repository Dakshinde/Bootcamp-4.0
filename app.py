import re
from pathlib import Path

import joblib
import pandas as pd
from flask import Flask, jsonify, render_template, request

BASE = Path(__file__).parent
app = Flask(__name__)

# ---------- ML model ----------
model = joblib.load(BASE / "placement_model.pkl")
FEATURES = list(model.feature_names_in_)  # column order the model was trained with

# form field name -> (model column, min, max, must_be_int)
FIELDS = {
    "cgpa":            ("CGPA",                 0, 10,  False),
    "coding_score":    ("Coding_Score",         0, 100, False),
    "aptitude_score":  ("Aptitude_Score",       0, 100, False),
    "projects":        ("Projects_Count",       0, 20,  True),
    "internships":     ("Internships",          0, 10,  True),
    "backlogs":        ("Backlogs",             0, 20,  True),
    "communication":   ("Communication_Rating", 1, 5,   False),
}


def tier_for(prob):
    if prob >= 70:
        return "Highly Likely", "Eligible for Tier-1 Drives"
    if prob >= 40:
        return "Moderately Likely", "Eligible for Tier-2 Drives"
    return "Unlikely", "Focus on Mass Recruiter Drives and skill building"


@app.post("/api/predict")
def predict():
    data = request.get_json(silent=True) or {}
    row = {}
    for key, (col, lo, hi, is_int) in FIELDS.items():
        try:
            val = float(data[key])
        except (KeyError, TypeError, ValueError):
            return jsonify(success=False, error=f"'{key}' is missing or not a number"), 400
        if not lo <= val <= hi:
            return jsonify(success=False, error=f"'{key}' must be between {lo} and {hi}"), 400
        if is_int and val != int(val):
            return jsonify(success=False, error=f"'{key}' must be a whole number"), 400
        row[col] = val

    X = pd.DataFrame([row], columns=FEATURES)  # keeps the training column order
    prob = float(model.predict_proba(X)[0][1]) * 100
    status, prediction = tier_for(prob)
    return jsonify(success=True, status=status, prediction=prediction,
                   probability=round(prob, 1))


# ---------- Policy chatbot (simple keyword retrieval) ----------
# Swap answer_question() for a FAISS + Groq call later; the route stays the same.
CHUNKS = [c.strip() for c in (BASE / "placement_rules.txt").read_text().split("\n\n") if c.strip()]
STOP = set("the a an is are of to for in on and or what who which how do does did get got can i my me it be with at by".split())


def words(text):
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP}


def answer_question(question):
    q = words(question)
    scored = sorted(((len(q & words(c)), c) for c in CHUNKS), reverse=True)
    if not q or scored[0][0] == 0:
        return "I couldn't find that in the placement policy, so I'd rather not guess. Try asking about eligibility, backlogs, tiers, or recruiters."
    return scored[0][1]


@app.post("/api/chat")
def chat():
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()
    if not message:
        return jsonify(success=False, error="Message is empty"), 400
    return jsonify(success=True, response=answer_question(message))


@app.get("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
