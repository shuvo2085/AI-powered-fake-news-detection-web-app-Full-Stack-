const API = 'http://localhost:5000/api';

async function checkStatus() {
  try {
    const r = await fetch(API + '/health', { signal: AbortSignal.timeout(2000) });
    if (r.ok) document.getElementById('dot').className = 'status-dot online';
  } catch {}
}

async function grabPage() {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const results = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => {
        const sel = document.querySelector('article') ||
                    document.querySelector('[role="main"]') ||
                    document.querySelector('.article-body') ||
                    document.querySelector('.post-content') ||
                    document.body;
        return sel ? sel.innerText.slice(0, 3000) : document.body.innerText.slice(0, 3000);
      }
    });
    if (results && results[0].result) {
      document.getElementById('articleText').value = results[0].result.trim();
    }
  } catch (e) {
    showError('Cannot grab page content. Try pasting manually.');
  }
}

async function analyze() {
  const text = document.getElementById('articleText').value.trim();
  if (!text || text.length < 20) {
    showError('Please enter or grab at least 20 characters of text.');
    return;
  }

  const btn = document.getElementById('analyzeBtn');
  btn.disabled = true;
  btn.textContent = '⏳ Analyzing...';
  hideError();

  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const res = await fetch(API + '/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, title: tab.title || 'Page Article', url: tab.url })
    });
    const data = await res.json();
    if (data.error) { showError(data.error); return; }
    displayResult(data);
  } catch {
    showError('Cannot connect to backend API. Make sure it is running on port 5000.');
  } finally {
    btn.disabled = false;
    btn.textContent = '🔍 Analyze';
  }
}

function displayResult(data) {
  const el = document.getElementById('resultEl');
  const v = data.verdict.toLowerCase();
  el.className = 'result visible ' + v;

  document.getElementById('verdictEl').className = 'verdict ' + v;
  document.getElementById('verdictEl').textContent = data.verdict + ' (' + data.confidence + '%)';
  document.getElementById('confLabel').textContent = 'Confidence: ' + data.confidence + '%';
  document.getElementById('confFill').style.width = data.confidence + '%';

  const flagsEl = document.getElementById('flagsEl');
  flagsEl.innerHTML = (data.flags || []).slice(0, 3).map(f =>
    `<div class="flag">⚠ ${f}</div>`).join('');

  const strEl = document.getElementById('strEl');
  strEl.innerHTML = (data.strengths || []).slice(0, 2).map(s =>
    `<div class="strength">✓ ${s}</div>`).join('');
}

function showError(msg) {
  const el = document.getElementById('errorEl');
  el.textContent = msg;
  el.style.display = 'block';
}
function hideError() {
  document.getElementById('errorEl').style.display = 'none';
}

function openApp() {
  chrome.tabs.create({ url: 'http://localhost:5500' });
}

checkStatus();
