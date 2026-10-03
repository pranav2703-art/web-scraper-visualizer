"""
visualizer.py
-------------
Generates and saves Matplotlib/Seaborn charts from a cleaned DataFrame.

Available charts
----------------
- sentiment_distribution  : doughnut chart of positive / neutral / negative counts
- top_authors             : horizontal bar chart of most-frequent authors
- text_length_histogram   : histogram of text character lengths
- tags_wordcloud          : word cloud of tag frequencies (requires `wordcloud` package)

Each function accepts a DataFrame and an output directory, saves a PNG, and
returns the file path so callers can log or display it.
"""

import logging
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

logger = logging.getLogger(__name__)

# ── Shared style ────────────────────────────────────────────────────────────
PALETTE = {
    "positive": "#639922",
    "neutral":  "#888780",
    "negative": "#E24B4A",
}
BAR_COLOR  = "#378ADD"
HIST_COLOR = "#5DCAA5"
FIG_DPI    = 150
FONT_SIZE  = 11

plt.rcParams.update({
    "font.size":        FONT_SIZE,
    "axes.spines.top":  False,
    "axes.spines.right":False,
    "figure.dpi":       FIG_DPI,
})


def _save(fig: plt.Figure, output_dir: Path, filename: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / filename
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved chart → %s", path)
    return path


# ── Individual chart functions ───────────────────────────────────────────────

def sentiment_distribution(df: pd.DataFrame, output_dir: Path) -> Path:
    """Doughnut chart showing proportion of each sentiment label."""
    if "sentiment" not in df.columns:
        raise ValueError("DataFrame must contain a 'sentiment' column.")

    counts = df["sentiment"].value_counts()
    labels = counts.index.tolist()
    colors = [PALETTE.get(label, "#CCCCCC") for label in labels]

    fig, ax = plt.subplots(figsize=(5, 5))
    wedges, texts, autotexts = ax.pie(
        counts,
        labels=labels,
        colors=colors,
        autopct="%1.0f%%",
        startangle=140,
        wedgeprops={"width": 0.55, "edgecolor": "white", "linewidth": 2},
    )
    for autotext in autotexts:
        autotext.set_fontsize(10)

    ax.set_title("Sentiment distribution", pad=16, fontweight="medium")
    return _save(fig, output_dir, "sentiment_distribution.png")


def top_authors(df: pd.DataFrame, output_dir: Path, top_n: int = 8) -> Path:
    """Horizontal bar chart of the most frequently appearing authors."""
    if "author" not in df.columns:
        raise ValueError("DataFrame must contain an 'author' column.")

    counts = df["author"].value_counts().head(top_n).sort_values()
    fig, ax = plt.subplots(figsize=(7, max(3, top_n * 0.45)))

    bars = ax.barh(counts.index, counts.values, color=BAR_COLOR, height=0.6)
    ax.bar_label(bars, padding=4, fontsize=10)
    ax.set_xlabel("Number of records")
    ax.set_title(f"Top {top_n} authors", fontweight="medium")
    ax.tick_params(axis="y", labelsize=10)
    ax.set_xlim(right=counts.max() * 1.15)

    return _save(fig, output_dir, "top_authors.png")


def text_length_histogram(df: pd.DataFrame, output_dir: Path, bins: int = 15) -> Path:
    """Histogram of text character lengths."""
    if "text_length" not in df.columns:
        if "text" in df.columns:
            df = df.copy()
            df["text_length"] = df["text"].str.len()
        else:
            raise ValueError("DataFrame must contain 'text_length' or 'text' column.")

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(df["text_length"].dropna(), bins=bins, color=HIST_COLOR, edgecolor="white", linewidth=0.8)
    ax.set_xlabel("Character length")
    ax.set_ylabel("Count")
    ax.set_title("Text length distribution", fontweight="medium")

    median = df["text_length"].median()
    ax.axvline(median, color="#E24B4A", linestyle="--", linewidth=1.2, label=f"Median: {median:.0f}")
    ax.legend(fontsize=10)

    return _save(fig, output_dir, "text_length_histogram.png")


def all_charts(df: pd.DataFrame, output_dir: Path) -> list[Path]:
    """
    Convenience wrapper — generate every available chart and return their paths.

    Parameters
    ----------
    df : pd.DataFrame
        Cleaned DataFrame from :mod:`cleaner`.
    output_dir : Path
        Directory where PNG files are written.

    Returns
    -------
    list[Path]
        Paths of the saved chart files.
    """
    generators = [sentiment_distribution, top_authors, text_length_histogram]
    paths = []
    for fn in generators:
        try:
            paths.append(fn(df, output_dir))
        except Exception as exc:  # noqa: BLE001
            logger.warning("Skipped %s: %s", fn.__name__, exc)
    return paths
