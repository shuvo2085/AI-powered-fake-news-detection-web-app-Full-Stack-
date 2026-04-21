# 🔍 TruthLens — AI Fake News Detector

A full-stack AI-powered fake news detection application with a web interface, REST API, MongoDB history, and a Chrome extension.

---

## 📁 Project Structure

```
fakenews/
├── backend/
│   ├── app.py              # Flask API + NLP engine
│   └── requirements.txt    # Python dependencies
├── frontend/
│   └── index.html          # Web UI (open in browser)
└── chrome_extension/
    ├── manifest.json
    ├── popup.html
    ├── popup.js
    ├── content.js
    ├── background.js
    └── icons/
```

---

## 🚀 Quick Start

### 1. Install MongoDB
- **Windows**: https://www.mongodb.com/try/download/community
- **Mac**: `brew tap mongodb/brew && brew install mongodb-community`
- **Linux**: `sudo apt install mongodb`

Start MongoDB:
```bash
mongod --dbpath /data/db
```

### 2. Set Up Python Backend

```bash
cd backend
pip install -r requirements.txt
python app.py
```

The API will start at **http://localhost:5000**

### 3. Open the Web App

Open `frontend/index.html` directly in your browser, **or** serve it:

```bash
# Option A: Python server
cd frontend
python -m http.server 5500
# Then open http://localhost:5500

# Option B: Just double-click index.html in your file explorer
```

---

## 🌐 Chrome Extension Setup

1. Open Chrome and go to `chrome://extensions/`
2. Enable **"Developer mode"** (top-right toggle)
3. Click **"Load unpacked"**
4. Select the `chrome_extension/` folder
5. The TruthLens icon will appear in your toolbar

**Usage:**
- Click the extension icon on any news page
- Click **"Grab Page"** to auto-extract article text
- Click **"Analyze"** to get the verdict

> ⚠️ Make sure the Python backend is running before using the extension.

---

## 🧠 How the NLP Detector Works

TruthLens uses a **multi-signal scoring system** (no ML training required):

| Signal | What it detects |
|--------|----------------|
| **Keyword Bank** | 40+ sensationalist terms (SHOCKING, BOMBSHELL, etc.) |
| **Credibility Markers** | Source citations, academic language, institution names |
| **CAPS Ratio** | Excessive capitalization (a hallmark of fake news) |
| **Punctuation Patterns** | Multiple `!!!` or `???` in sequence |
| **Regex Patterns** | Click-bait phrases, share-bait, conspiracy language |
| **Readability Score** | Flesch-Kincaid approximation |
| **Source URLs** | Trusted domains (Reuters, BBC, AP, etc.) |
| **Article Length** | Very short articles penalized |

**Verdict logic:**
- `FAKE` → fake signals dominate (65%+ of total score)
- `REAL` → credibility signals dominate (65%+ of total score)
- `UNCERTAIN` → mixed or insufficient signals

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/analyze` | Analyze an article |
| `GET` | `/api/history` | Get analysis history |
| `DELETE` | `/api/history/<id>` | Delete a history item |
| `GET` | `/api/stats` | Get aggregate stats |
| `GET` | `/api/health` | Health check |

### Example: Analyze an article
```bash
curl -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "text": "SHOCKING: Scientists EXPOSED for hiding miracle cure! Share before deleted!!",
    "title": "Test Article",
    "url": "https://example.com"
  }'
```

**Response:**
```json
{
  "verdict": "FAKE",
  "confidence": 91,
  "fake_score": 28,
  "real_score": 2,
  "flags": ["Sensationalist term: Shocking", "High caps ratio"],
  "strengths": [],
  "word_count": 11,
  "readability": 72.1,
  "caps_ratio": 36.0
}
```

---

## ⚙️ Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MONGO_URI` | `mongodb://localhost:27017/` | MongoDB connection string |

For MongoDB Atlas (cloud):
```bash
MONGO_URI="mongodb+srv://user:pass@cluster.mongodb.net/" python app.py
```

---

## 🎨 Features

- ✅ Real-time fake news analysis
- ✅ Confidence score with visual bar
- ✅ Red flags & credibility signals breakdown
- ✅ Article metrics (word count, readability, CAPS ratio)
- ✅ Full history with MongoDB persistence
- ✅ History filtering (All / Fake / Real / Uncertain)
- ✅ Pagination for history
- ✅ Live API health indicator
- ✅ Global stats dashboard
- ✅ Chrome extension with page-grab
- ✅ Keyboard shortcut: Ctrl+Enter to analyze
- ✅ CORS enabled for browser use

---

## 📦 Tech Stack

- **Backend**: Python 3, Flask, Flask-CORS
- **Database**: MongoDB (pymongo)
- **NLP**: Custom multi-signal scoring (no ML model required)
- **Frontend**: Vanilla HTML/CSS/JS
- **Extension**: Chrome Manifest V3

---

## 🔧 Troubleshooting

**"API Offline" shown in app:**
- Make sure `python app.py` is running
- Check terminal for errors
- Try visiting http://localhost:5000/api/health

**MongoDB connection error:**
- Ensure MongoDB service is running: `mongod`
- Check if port 27017 is available

**Chrome extension won't load:**
- Make sure Developer Mode is ON
- Re-load after any file changes
- Check the extension error log in `chrome://extensions/`
