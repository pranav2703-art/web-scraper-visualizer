"""
cleaner.py
----------
Ingests raw scrape records, cleans them with Pandas, and returns a typed DataFrame.

Cleaning steps applied:
  1. Flatten ScrapeResult lists into a single DataFrame.
  2. Strip leading/trailing whitespace from all string columns.
  3. Normalise author names (title-case, collapse internal spaces).
  4. Drop fully duplicate rows.
  5. Fill or flag missing values.
  6. Add derived columns: text_length, sentiment_score, scraped_at.
"""

import logging
import re
from datetime import datetime, timezone

import pandas as pd

from scraper import ScrapeResult

logger = logging.getLogger(__name__)

# Simple keyword-based sentiment (replace with a real model if needed)
_POSITIVE_WORDS = frozenset(
    ["love", "courage", "beautiful", "genius", "joy", "wonder", "miracle",
     "success", "value", "great", "good", "better", "best", "right", "possible"]
)
_NEGATIVE_WORDS = frozenset(
    ["boring", "stupid", "failure", "hate", "never", "ridiculous",
     "impossible", "wrong", "knocked", "bad", "worse", "worst"]
)


def _sentiment(text: str) -> str:
    words = set(re.findall(r"\b\w+\b", text.lower()))
    score = len(words & _POSITIVE_WORDS) - len(words & _NEGATIVE_WORDS)
    if score > 0:
        return "positive"
    if score < 0:
        return "negative"
    return "neutral"


def flatten_results(results: list[ScrapeResult]) -> pd.DataFrame:
    """Combine records from all ScrapeResult objects into one DataFrame."""
    rows = []
    for result in results:
        for record in result.records:
            rows.append({"source_url": result.url, **record})
    if not rows:
        logger.warning("No records to flatten — returning empty DataFrame.")
        return pd.DataFrame()
    return pd.DataFrame(rows)


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """
    Run the full cleaning pipeline on a raw DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Output of :func:`flatten_results`.

    Returns
    -------
    pd.DataFrame
        Cleaned DataFrame with derived columns appended.
    """
    if df.empty:
        return df

    original_len = len(df)

    # 1. Strip whitespace from every string column
    str_cols = df.select_dtypes(include="object").columns
    df[str_cols] = df[str_cols].apply(lambda col: col.str.strip())

    # 2. Normalise author names
    if "author" in df.columns:
        df["author"] = (
            df["author"]
            .str.replace(r"\s+", " ", regex=True)
            .str.title()
            .str.replace(r"^by\s+", "", flags=re.IGNORECASE, regex=True)
        )

    # 3. Drop exact duplicates
    df.drop_duplicates(inplace=True)
    dropped = original_len - len(df)
    if dropped:
        logger.info("Dropped %d duplicate row(s).", dropped)

    # 4. Handle missing values
    df.fillna({"tags": "untagged", "author": "Unknown"}, inplace=True)
    remaining_nulls = df.isnull().sum().sum()
    if remaining_nulls:
        logger.warning("%d null value(s) remain after fill.", remaining_nulls)

    # 5. Derived columns
    if "text" in df.columns:
        df["text_length"] = df["text"].str.len()
        df["sentiment"] = df["text"].apply(_sentiment)

    df["scraped_at"] = datetime.now(tz=timezone.utc).isoformat()

    # 6. Reset index for a clean integer index
    df.reset_index(drop=True, inplace=True)
    logger.info("Cleaning complete. Final shape: %s", df.shape)

    return df
