"""
main.py
-------
Entry point for the Web Scraper & Visualizer pipeline.

Usage
-----
    python main.py                          # run with defaults
    python main.py --urls URL1 URL2         # scrape specific URLs
    python main.py --output results/        # custom output directory
    python main.py --export csv json        # export cleaned data
    python main.py --no-charts              # skip chart generation

Example
-------
    python main.py \\
        --urls https://quotes.toscrape.com \\
        --export csv \\
        --output output/
"""

import argparse
import logging
import sys
from pathlib import Path

from cleaner import clean, flatten_results
from scraper import ScraperConfig, scrape
from visualizer import all_charts

# ── Logging setup ────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# ── Default scrape config ────────────────────────────────────────────────────
DEFAULT_URLS = ["https://quotes.toscrape.com"]
DEFAULT_SELECTORS = {
    "text":   "span.text",
    "author": "small.author",
    "tags":   "div.tags",
}


# ── CLI ──────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Scrape web data, clean it with Pandas, and visualise with Matplotlib.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--urls", nargs="+", default=DEFAULT_URLS,
        metavar="URL", help="One or more URLs to scrape (default: quotes.toscrape.com)."
    )
    parser.add_argument(
        "--output", default="output", metavar="DIR",
        help="Directory for charts and exports (default: ./output)."
    )
    parser.add_argument(
        "--export", nargs="*", choices=["csv", "json"], default=[],
        metavar="FORMAT", help="Export cleaned data as csv and/or json."
    )
    parser.add_argument(
        "--no-charts", action="store_true",
        help="Skip chart generation."
    )
    parser.add_argument(
        "--retries", type=int, default=3, metavar="N",
        help="Max retries per URL on failure (default: 3)."
    )
    parser.add_argument(
        "--delay", type=float, default=1.0, metavar="SECS",
        help="Pause between requests in seconds (default: 1.0)."
    )
    return parser


# ── Pipeline ─────────────────────────────────────────────────────────────────

def run(args: argparse.Namespace) -> None:
    output_dir = Path(args.output)

    # 1. Scrape
    logger.info("=" * 50)
    logger.info("STEP 1 — Scraping %d URL(s)", len(args.urls))
    config = ScraperConfig(
        urls=args.urls,
        css_selectors=DEFAULT_SELECTORS,
        max_retries=args.retries,
        delay_between_requests=args.delay,
    )
    results = scrape(config)
    total_raw = sum(len(r.records) for r in results)
    logger.info("Scraped %d raw record(s) across %d source(s).", total_raw, len(results))

    # 2. Clean
    logger.info("=" * 50)
    logger.info("STEP 2 — Cleaning with Pandas")
    raw_df = flatten_results(results)
    df = clean(raw_df)

    if df.empty:
        logger.warning("No data after cleaning — exiting.")
        sys.exit(0)

    # 3. Export
    if args.export:
        logger.info("=" * 50)
        logger.info("STEP 3 — Exporting data")
        output_dir.mkdir(parents=True, exist_ok=True)

        if "csv" in args.export:
            csv_path = output_dir / "scraped_data.csv"
            df.to_csv(csv_path, index=False)
            logger.info("CSV  → %s", csv_path)

        if "json" in args.export:
            json_path = output_dir / "scraped_data.json"
            df.to_json(json_path, orient="records", indent=2, force_ascii=False)
            logger.info("JSON → %s", json_path)

    # 4. Visualise
    if not args.no_charts:
        logger.info("=" * 50)
        logger.info("STEP 4 — Generating visualisations")
        chart_paths = all_charts(df, output_dir / "charts")
        logger.info("Generated %d chart(s).", len(chart_paths))

    logger.info("=" * 50)
    logger.info("Done. Output written to: %s", output_dir.resolve())


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
