from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime
import re
import math
import os
import hashlib

app = Flask(__name__)
CORS(app)

# MongoDB connection
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI)
db = client["fakenews_db"]
history_col = db["history"]

# ─── NLP Fake News Classifier ─────────────────────────────────────────────────

# Weighted keyword banks
FAKE_SIGNALS = {
    # Sensationalist language
    "SHOCKING": 3, "BOMBSHELL": 3, "BREAKING": 1, "EXPLOSIVE": 3,
    "YOU WON'T BELIEVE": 4, "THEY DON'T WANT YOU TO KNOW": 5,
    "WAKE UP": 3, "SHEEPLE": 5, "TRUTH BOMB": 4, "EXPOSED": 2,
    "DEEP STATE": 5, "ILLUMINATI": 5, "NEW WORLD ORDER": 5,
    "CHEMTRAILS": 5, "FALSE FLAG": 4, "CRISIS ACTOR": 5,
    "MAINSTREAM MEDIA LIES": 5, "MSM": 2, "FAKE NEWS": 2,
    "HOAX": 3, "COVER-UP": 3, "CONSPIRACY": 2,
    # Emotional manipulation
    "OUTRAGE": 2, "DISGUSTING": 2, "MUST SHARE": 4, "SHARE BEFORE DELETED": 5,
    "URGENT": 2, "ACT NOW": 2, "BEFORE IT'S TOO LATE": 3,
    # Pseudoscience
    "CURE": 1, "MIRACLE": 3, "SECRET REMEDY": 4, "DOCTORS HATE": 4,
    "100% PROVEN": 4, "SCIENTIFICALLY PROVEN": 1, "THEY'RE HIDING": 4,
    # Anonymous sourcing
    "SOURCES SAY": 1, "INSIDERS REVEAL": 3, "ANONYMOUS SOURCES": 1,
    "RUMORED": 2, "ALLEGEDLY": 1, "REPORTEDLY": 1,
    # Click-bait patterns
    "TOP SECRET": 3, "CLASSIFIED": 2, "LEAKED": 2,
    "WHAT THEY AREN'T TELLING YOU": 5, "THE REAL TRUTH": 3,
}

REAL_SIGNALS = {
    # Credible sourcing
    "ACCORDING TO": 2, "RESEARCH SHOWS": 2, "STUDY FINDS": 2,
    "PUBLISHED IN": 3, "PEER-REVIEWED": 4, "JOURNAL": 2,
    "UNIVERSITY": 2, "INSTITUTE": 1, "PROFESSOR": 1,
    "SPOKESPERSON": 2, "OFFICIAL STATEMENT": 3, "PRESS RELEASE": 2,
    # Measured language
    "SUGGESTS": 2, "INDICATES": 2, "ANALYSIS": 2, "DATA": 1,
    "EVIDENCE": 2, "INVESTIGATION": 2, "REPORT": 1, "SURVEY": 2,
    # Institutions
    "WHO": 1, "CDC": 2, "FDA": 2, "REUTERS": 3, "AP NEWS": 3,
    "BBC": 2, "NPR": 2, "ASSOCIATED PRESS": 3, "THE NEW YORK TIMES": 2,
    "WASHINGTON POST": 2, "COURT": 2, "PARLIAMENT": 2, "SENATE": 2,
    "CONGRESS": 2, "GOVERNMENT": 1, "DEPARTMENT": 1, "MINISTRY": 1,
}

FAKE_PATTERNS = [
    (r'\b(!!+|\?{2,})', 2),                    # Multiple ! or ?
    (r'\bALL CAPS WORD\b', 1),                 # handled separately
    (r'\b\d+% of \w+ AGREE\b', 3),             # fake stats
    (r'\bshare (this|before|now)\b', 4),       # share-bait
    (r'\bwake up\b', 3),
    (r'\bthey (don\'t|won\'t) want you\b', 5),
    (r'\bsecret (cure|method|trick|remedy)\b', 4),
    (r'\bdoctors (hate|don\'t want)\b', 4),
    (r'\bclick here\b', 2),
    (r'\bgoing viral\b', 2),
]

REAL_PATTERNS = [
    (r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b', 2),  # dates
    (r'\b(said|stated|confirmed|announced|reported|told reporters)\b', 2),
    (r'\b(percent|%)\b.*\b(study|survey|poll)\b', 2),
    (r'\baccording to\b', 2),
    (r'\bpeer.reviewed\b', 4),
    (r'\bstatistically\b', 2),
    (r'https?://(www\.)?(reuters|apnews|bbc|npr|nytimes|washingtonpost|theguardian)\.', 3),
]


def count_caps_ratio(text):
    words = text.split()
    if not words:
        return 0
    caps = sum(1 for w in words if w.isupper() and len(w) > 2)
    return caps / len(words)


def count_exclamations(text):
    return text.count('!') + text.count('?')


def readability_score(text):
    """Simple Flesch-Kincaid approximation."""
    sentences = re.split(r'[.!?]+', text)
    sentences = [s for s in sentences if s.strip()]
    words = text.split()
    if not sentences or not words:
        return 50
    avg_words = len(words) / len(sentences)
    syllables = sum(count_syllables(w) for w in words)
    avg_syl = syllables / len(words)
    score = 206.835 - 1.015 * avg_words - 84.6 * avg_syl
    return max(0, min(100, score))


def count_syllables(word):
    word = word.lower()
    count = 0
    vowels = 'aeiouy'
    prev_vowel = False
    for char in word:
        is_vowel = char in vowels
        if is_vowel and not prev_vowel:
            count += 1
        prev_vowel = is_vowel
    if word.endswith('e'):
        count -= 1
    return max(1, count)


def analyze_article(text):
    text_upper = text.upper()
    text_lower = text.lower()

    fake_score = 0
    real_score = 0
    flags = []
    strengths = []

    # Keyword scoring
    for kw, weight in FAKE_SIGNALS.items():
        if kw in text_upper:
            fake_score += weight
            flags.append(f'Sensationalist term: "{kw.title()}"')

    for kw, weight in REAL_SIGNALS.items():
        if kw in text_upper:
            real_score += weight
            strengths.append(f'Credible indicator: "{kw.title()}"')

    # Pattern scoring
    for pattern, weight in FAKE_PATTERNS:
        if re.search(pattern, text_lower):
            fake_score += weight
            flags.append(f'Detected pattern: {pattern}')

    for pattern, weight in REAL_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            real_score += weight
            strengths.append(f'Reliable pattern found')

    # CAPS ratio penalty
    caps_ratio = count_caps_ratio(text)
    if caps_ratio > 0.3:
        penalty = int(caps_ratio * 10)
        fake_score += penalty
        flags.append(f'High caps ratio ({caps_ratio:.0%}) — sensationalist writing')

    # Exclamation penalty
    excl = count_exclamations(text)
    if excl > 3:
        fake_score += min(excl, 8)
        flags.append(f'{excl} exclamation/question marks — emotional manipulation')

    # Readability
    readability = readability_score(text)
    if readability > 70:
        real_score += 2
        strengths.append('Clear, readable prose')
    elif readability < 30:
        fake_score += 2
        flags.append('Unusually complex or garbled language')

    # Article length check
    word_count = len(text.split())
    if word_count < 50:
        fake_score += 3
        flags.append('Very short article — lack of depth')
    elif word_count > 300:
        real_score += 2
        strengths.append('Substantial article length')

    # Final verdict
    total = fake_score + real_score
    if total == 0:
        confidence = 50
        verdict = "UNCERTAIN"
    else:
        fake_pct = (fake_score / total) * 100
        real_pct = (real_score / total) * 100

        if fake_pct >= 65:
            verdict = "FAKE"
            confidence = min(99, int(fake_pct))
        elif real_pct >= 65:
            verdict = "REAL"
            confidence = min(99, int(real_pct))
        else:
            verdict = "UNCERTAIN"
            confidence = max(int(fake_pct), int(real_pct))

    return {
        "verdict": verdict,
        "confidence": confidence,
        "fake_score": fake_score,
        "real_score": real_score,
        "flags": flags[:6],
        "strengths": strengths[:6],
        "word_count": word_count,
        "readability": round(readability, 1),
        "caps_ratio": round(caps_ratio * 100, 1),
    }


# ─── API Routes ────────────────────────────────────────────────────────────────

@app.route("/api/analyze", methods=["POST"])
def analyze():
    data = request.json
    text = data.get("text", "").strip()
    title = data.get("title", "Untitled Article").strip()
    url = data.get("url", "").strip()

    if not text or len(text) < 20:
        return jsonify({"error": "Please provide at least 20 characters of article text."}), 400

    result = analyze_article(text)

    # Save to MongoDB
    doc = {
        "title": title[:200],
        "text": text[:2000],
        "url": url,
        "verdict": result["verdict"],
        "confidence": result["confidence"],
        "fake_score": result["fake_score"],
        "real_score": result["real_score"],
        "flags": result["flags"],
        "strengths": result["strengths"],
        "word_count": result["word_count"],
        "readability": result["readability"],
        "timestamp": datetime.utcnow().isoformat(),
        "hash": hashlib.md5(text[:500].encode()).hexdigest()
    }
    inserted = history_col.insert_one(doc)
    result["id"] = str(inserted.inserted_id)
    result["timestamp"] = doc["timestamp"]

    return jsonify(result)


@app.route("/api/history", methods=["GET"])
def get_history():
    limit = int(request.args.get("limit", 20))
    skip = int(request.args.get("skip", 0))
    verdict_filter = request.args.get("verdict", None)

    query = {}
    if verdict_filter and verdict_filter in ["FAKE", "REAL", "UNCERTAIN"]:
        query["verdict"] = verdict_filter

    total = history_col.count_documents(query)
    docs = list(history_col.find(query, {"text": 0})
                .sort("timestamp", -1)
                .skip(skip)
                .limit(limit))

    for d in docs:
        d["_id"] = str(d["_id"])

    return jsonify({"total": total, "results": docs})


@app.route("/api/history/<doc_id>", methods=["DELETE"])
def delete_history(doc_id):
    from bson import ObjectId
    try:
        history_col.delete_one({"_id": ObjectId(doc_id)})
        return jsonify({"success": True})
    except Exception:
        return jsonify({"error": "Invalid ID"}), 400


@app.route("/api/stats", methods=["GET"])
def get_stats():
    total = history_col.count_documents({})
    fake = history_col.count_documents({"verdict": "FAKE"})
    real = history_col.count_documents({"verdict": "REAL"})
    uncertain = history_col.count_documents({"verdict": "UNCERTAIN"})

    avg_conf = list(history_col.aggregate([
        {"$group": {"_id": None, "avg": {"$avg": "$confidence"}}}
    ]))
    avg_confidence = round(avg_conf[0]["avg"], 1) if avg_conf else 0

    return jsonify({
        "total": total,
        "fake": fake,
        "real": real,
        "uncertain": uncertain,
        "avg_confidence": avg_confidence
    })


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "version": "1.0.0"})


if __name__ == "__main__":
    app.run(debug=True, port=5000, host="0.0.0.0")
