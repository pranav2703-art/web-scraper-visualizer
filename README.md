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

## Project Structure

```
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
