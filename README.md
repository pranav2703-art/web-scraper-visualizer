<<<<<<< HEAD
# DataPull — Web Scraper & Visualizer

Full-stack web app with a **Flask** backend and an immersive dark-mode frontend.

## Stack

| Layer     | Tech                                      |
|-----------|-------------------------------------------|
| Backend   | Python · Flask · BeautifulSoup · requests |
| Frontend  | Vanilla JS · Chart.js · Space Grotesk     |
| Charts    | Chart.js 4 (sentiment, authors, histogram)|
| Styling   | Custom CSS · dark theme · CSS variables   |
=======
# Web Scraper & Visualizer

Automated data extraction from multiple web sources using **BeautifulSoup**, cleaned with **Pandas**, and visualized with **Matplotlib**.

## Features

- Multi-URL scraping with configurable CSS selectors
- Retry logic with configurable delays (polite scraping)
- Pandas cleaning pipeline: deduplication, whitespace normalization, null handling
- Derived columns: `text_length`, `sentiment`
- Three Matplotlib charts: sentiment doughnut, top-authors bar, text-length histogram
- CSV and JSON export
- Full CLI with `argparse`
>>>>>>> 4897f25361eceee72898006737aca052eaeb120a

## Project Structure

```
<<<<<<< HEAD
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
=======
web-scraper-visualizer/
├── src/
│   ├── scraper.py        # HTTP fetching + BeautifulSoup parsing
│   ├── cleaner.py        # Pandas cleaning pipeline
│   ├── visualizer.py     # Matplotlib chart generation
│   └── main.py           # CLI entry point
├── tests/
│   └── test_cleaner.py   # pytest unit tests
├── output/               # generated charts + exports (git-ignored)
├── requirements.txt
└── README.md
```

## Setup

```bash
# 1. Clone
git clone https://github.com/yourusername/web-scraper-visualizer.git
cd web-scraper-visualizer

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
# Run with defaults (scrapes quotes.toscrape.com)
python src/main.py

# Scrape a custom URL and export both CSV and JSON
python src/main.py --urls https://quotes.toscrape.com --export csv json

# Skip chart generation, write output to a custom directory
python src/main.py --no-charts --output results/

# All options
python src/main.py --help
```

### CLI Options

| Flag | Default | Description |
|---|---|---|
| `--urls` | quotes.toscrape.com | One or more URLs to scrape |
| `--output` | `output/` | Directory for charts and exports |
| `--export` | _(none)_ | `csv`, `json`, or both |
| `--no-charts` | false | Skip chart generation |
| `--retries` | `3` | Max retries per URL |
| `--delay` | `1.0` | Seconds between requests |

## Extending the Scraper

To scrape a different site, update `DEFAULT_SELECTORS` in `main.py`:

```python
DEFAULT_SELECTORS = {
    "title":  "h2.product-title",
    "price":  "span.price",
    "rating": "div.star-rating",
}
```

CSS selectors follow standard BeautifulSoup syntax.

## Running Tests

```bash
pytest tests/ -v --cov=src
```

## Output

After a successful run the `output/` directory contains:

```
output/
├── scraped_data.csv          # if --export csv
├── scraped_data.json         # if --export json
└── charts/
    ├── sentiment_distribution.png
    ├── top_authors.png
    └── text_length_histogram.png
```

## License

MIT
>>>>>>> 4897f25361eceee72898006737aca052eaeb120a
