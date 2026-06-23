"""
tests/test_cleaner.py
---------------------
Unit tests for the cleaning pipeline.
"""

import pandas as pd
import pytest

from src.cleaner import _sentiment, clean, flatten_results
from src.scraper import ScrapeResult


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_results():
    return [
        ScrapeResult(
            url="https://example.com",
            records=[
                {"text": "  Life is beautiful.  ", "author": "  jane austen  ", "tags": "life"},
                {"text": "Failure teaches success.", "author": "Edison", "tags": None},
                {"text": "Life is beautiful.", "author": "Jane Austen", "tags": "life"},  # duplicate
            ],
            status_code=200,
            elapsed_ms=123.0,
        )
    ]


@pytest.fixture
def raw_df(sample_results):
    return flatten_results(sample_results)


# ── flatten_results ───────────────────────────────────────────────────────────

class TestFlattenResults:
    def test_returns_dataframe(self, sample_results):
        df = flatten_results(sample_results)
        assert isinstance(df, pd.DataFrame)

    def test_row_count(self, sample_results):
        df = flatten_results(sample_results)
        assert len(df) == 3

    def test_source_url_column_added(self, sample_results):
        df = flatten_results(sample_results)
        assert "source_url" in df.columns

    def test_empty_results_returns_empty_df(self):
        df = flatten_results([])
        assert df.empty


# ── clean ─────────────────────────────────────────────────────────────────────

class TestClean:
    def test_strips_whitespace(self, raw_df):
        df = clean(raw_df)
        assert df["text"].str.startswith(" ").any() is False

    def test_normalises_author(self, raw_df):
        df = clean(raw_df)
        assert "Jane Austen" in df["author"].values

    def test_drops_duplicates(self, raw_df):
        df = clean(raw_df)
        assert len(df) == 2

    def test_fills_missing_tags(self, raw_df):
        df = clean(raw_df)
        assert df["tags"].isnull().sum() == 0
        assert "untagged" in df["tags"].values

    def test_adds_text_length(self, raw_df):
        df = clean(raw_df)
        assert "text_length" in df.columns
        assert (df["text_length"] > 0).all()

    def test_adds_sentiment(self, raw_df):
        df = clean(raw_df)
        assert "sentiment" in df.columns
        assert set(df["sentiment"]).issubset({"positive", "neutral", "negative"})

    def test_empty_input_returns_empty(self):
        df = clean(pd.DataFrame())
        assert df.empty


# ── _sentiment ────────────────────────────────────────────────────────────────

class TestSentiment:
    @pytest.mark.parametrize("text,expected", [
        ("Life is beautiful and full of joy.", "positive"),
        ("Failure and hate make things worse.", "negative"),
        ("The sky is blue.", "neutral"),
    ])
    def test_basic_cases(self, text, expected):
        assert _sentiment(text) == expected
