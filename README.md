# DataPull — Web Scraper & Visualizer

Full-stack web app with a **Flask** backend and an immersive dark-mode frontend.

## Stack

| Layer     | Tech                                      |
|-----------|-------------------------------------------|
| Backend   | Python · Flask · BeautifulSoup · requests |
| Frontend  | Vanilla JS · Chart.js · Space Grotesk     |
| Charts    | Chart.js 4 (sentiment, authors, histogram)|
| Styling   | Custom CSS · dark theme · CSS variables   |

## Project Structure

```
scraper-app/
├── app.py                  # Flask API + scraping logic
├── requirements.txt
├── README.md
├── templates/
│   └── index.html          # Main SPA shell
└── static/
    ├── css/style.css       # Dark theme, layout, animations
    └── js/app.js           # Nav, scrape flow, charts, table
```

## Setup & Run

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start the server
python app.py

# 3. Open in browser
# → http://localhost:5000
```

## API Endpoints

| Method | Endpoint             | Description                        |
|--------|----------------------|------------------------------------|
| GET    | `/`                  | Serve the frontend                 |
| POST   | `/api/scrape`        | Scrape a URL, return records+stats |
| GET    | `/api/history`       | Last 20 scrape sessions            |
| GET    | `/api/export/csv`    | Download last scrape as CSV        |
| GET    | `/api/export/json`   | Download last scrape as JSON       |

### POST /api/scrape

**Request body:**
```json
{ "url": "https://quotes.toscrape.com" }
```

**Response:**
```json
{
  "records": [{ "text": "...", "author": "...", "tags": "...", "length": 80, "sentiment": "positive" }],
  "stats":   { "total": 10, "sentiment": {...}, "top_authors": [...], "avg_length": 95, "length_bins": [...] },
  "session": { "id": 1, "url": "...", "records": 10, "elapsed_ms": 412, "scraped_at": "..." }
}
```

## Features

- Live progress log with simulated pipeline steps
- Animated ambient particle background
- Four panels: Scraper · Charts · Data Table · History
- Real-time table filter
- CSV / JSON export
- Persistent scrape history (in-memory, per server run)
