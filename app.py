"""
app.py  —  Flask backend for Web Scraper & Visualizer
======================================================
Endpoints
---------
POST /api/scrape          Scrape a URL, return cleaned records + stats
GET  /api/history         Return past scrape sessions (in-memory store)
GET  /api/export/<fmt>    Download last scrape as csv or json
GET  /                    Serve the frontend
"""

import io
import json
import re
import time
from datetime import datetime, timezone
from typing import Any

import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify, render_template, request, send_file
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ── In-memory session store ──────────────────────────────────────────────────
_history: list[dict] = []
_last_records: list[dict] = []

# ── Sentiment ────────────────────────────────────────────────────────────────
_POS = frozenset(["love","courage","beautiful","genius","joy","wonder","miracle",
                   "success","value","great","good","better","best","right","possible",
                   "happy","hope","light","dream","inspire","freedom"])
_NEG = frozenset(["boring","stupid","failure","hate","never","ridiculous",
                   "impossible","wrong","knocked","bad","worse","worst","dark",
                   "pain","fear","lost","broken","lie","fake"])

def _sentiment(text: str) -> str:
    words = set(re.findall(r"\b\w+\b", text.lower()))
    score = len(words & _POS) - len(words & _NEG)
    return "positive" if score > 0 else "negative" if score < 0 else "neutral"


# ── Scraping helpers ─────────────────────────────────────────────────────────
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ScraperApp/1.0)"}


def _fetch_page(url: str) -> requests.Response:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=12, allow_redirects=True)
    except requests.exceptions.RequestException as exc:
        raise requests.exceptions.RequestException(f"Could not reach {url}: {exc}") from exc

    if resp.status_code == 403:
        raise PermissionError(
            f"This site blocks automated scraping (HTTP 403). Try a public page that allows bots, like https://quotes.toscrape.com."
        )
    resp.raise_for_status()
    return resp


def _scrape_quotes(url: str) -> list[dict]:
    resp = _fetch_page(url)
    soup = BeautifulSoup(resp.text, "html.parser")
    records = []
    for q in soup.select("div.quote"):
        text   = q.select_one("span.text")
        author = q.select_one("small.author")
        tags   = [t.get_text() for t in q.select("a.tag")]
        if text:
            raw = text.get_text(strip=True).strip("\u201c\u201d")
            records.append({
                "text":      raw,
                "author":    author.get_text(strip=True) if author else "Unknown",
                "tags":      ", ".join(tags) if tags else "untagged",
                "length":    len(raw),
                "sentiment": _sentiment(raw),
            })
    return records


def _scrape_generic(url: str) -> list[dict]:
    """Fallback: grab all paragraph text from any page."""
    resp = _fetch_page(url)
    soup = BeautifulSoup(resp.text, "html.parser")
    records = []
    for p in soup.select("p"):
        raw = p.get_text(strip=True)
        if len(raw) > 30:
            records.append({
                "text":      raw[:300],
                "author":    soup.title.string if soup.title else "–",
                "tags":      "scraped",
                "length":    len(raw),
                "sentiment": _sentiment(raw),
            })
    return records[:30]


def _build_stats(records: list[dict]) -> dict[str, Any]:
    if not records:
        return {}
    sent = {"positive": 0, "neutral": 0, "negative": 0}
    author_counts: dict[str, int] = {}
    lengths = []
    for r in records:
        sent[r["sentiment"]] = sent.get(r["sentiment"], 0) + 1
        author_counts[r["author"]] = author_counts.get(r["author"], 0) + 1
        lengths.append(r["length"])
    top_authors = sorted(author_counts.items(), key=lambda x: -x[1])[:8]
    avg_len = round(sum(lengths) / len(lengths))
    bins = [0, 0, 0, 0, 0]
    for l in lengths:
        bins[min(l // 40, 4)] += 1
    return {
        "total":       len(records),
        "sentiment":   sent,
        "top_authors": [{"name": a, "count": c} for a, c in top_authors],
        "avg_length":  avg_len,
        "length_bins": bins,
    }


# ── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/scrape", methods=["POST"])
def scrape():
    global _last_records
    body = request.get_json(force=True)
    url  = (body.get("url") or "").strip()
    if not url:
        return jsonify({"error": "url is required"}), 400

    t0 = time.monotonic()
    try:
        if "toscrape.com" in url:
            records = _scrape_quotes(url)
        else:
            records = _scrape_generic(url)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 502

    elapsed = round((time.monotonic() - t0) * 1000)
    stats   = _build_stats(records)
    _last_records = records

    session = {
        "id":         len(_history) + 1,
        "url":        url,
        "records":    len(records),
        "elapsed_ms": elapsed,
        "scraped_at": datetime.now(tz=timezone.utc).isoformat(),
    }
    _history.append(session)

    return jsonify({
        "records": records,
        "stats":   stats,
        "session": session,
    })


@app.route("/api/history")
def history():
    return jsonify(_history[-20:])


@app.route("/api/export/<fmt>")
def export(fmt: str):
    if not _last_records:
        return jsonify({"error": "Nothing scraped yet"}), 404
    if fmt == "csv":
        lines = ["id,text,author,tags,sentiment,length"]
        for i, r in enumerate(_last_records, 1):
            text = r["text"].replace('"', '""')
            lines.append(f'{i},"{text}","{r["author"]}","{r["tags"]}",{r["sentiment"]},{r["length"]}')
        buf = io.BytesIO("\n".join(lines).encode())
        return send_file(buf, mimetype="text/csv",
                         as_attachment=True, download_name="scraped_data.csv")
    if fmt == "json":
        buf = io.BytesIO(json.dumps(_last_records, indent=2).encode())
        return send_file(buf, mimetype="application/json",
                         as_attachment=True, download_name="scraped_data.json")
    return jsonify({"error": "fmt must be csv or json"}), 400


if __name__ == "__main__":
    app.run(debug=True, port=5000)
