from __future__ import annotations

import pandas as pd

from .config import NEGATIVE_WORDS, POSITIVE_WORDS
from .data_loader import normalize_dataframe


def get_sentiment(row) -> str:
    text = str(row["review_text"]).lower()
    neg = sum(word in text for word in NEGATIVE_WORDS)
    pos = sum(word in text for word in POSITIVE_WORDS)
    rating = row["rating"]

    if pd.notna(rating):
        if rating <= 2:
            return "Negative"
        if rating >= 4:
            return "Positive"
    if neg > pos:
        return "Negative"
    if pos > neg:
        return "Positive"
    return "Neutral"


def add_analysis(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    result["sentiment"] = result.apply(get_sentiment, axis=1)
    return result


def severity(freq_percent: float, negative_percent: float) -> str:
    if freq_percent >= 30 or negative_percent >= 80:
        return "HIGH"
    if freq_percent >= 20 or negative_percent >= 60:
        return "MEDIUM"
    return "LOW"


def priority_score(freq_percent: float, negative_percent: float, severity_name: str, trend: float) -> int:
    severity_score = {"HIGH": 100, "MEDIUM": 65, "LOW": 35}.get(severity_name, 35)
    trend_score = min(abs(trend) * 2, 100)
    return int(round(
        0.40 * min(freq_percent, 100)
        + 0.30 * min(negative_percent, 100)
        + 0.20 * severity_score
        + 0.10 * trend_score
    ))


def analyze_reviews(raw_df: pd.DataFrame, assume_normalized: bool = False, loader_info: dict | None = None):
    """Analyze a ReviewLens dataframe.

    When the ingestion layer has already normalized the dataframe, pass
    ``assume_normalized=True`` and optional ``loader_info`` so uploaded data
    is not normalized twice.
    """
    if assume_normalized:
        normalized = raw_df.copy()
        if "date" in normalized.columns and not pd.api.types.is_datetime64_any_dtype(normalized["date"]):
            normalized["date"] = pd.to_datetime(normalized["date"], errors="coerce")
        has_dates = bool("date" in normalized.columns and normalized["date"].notna().sum() > 0)
        info = {
            "mapped_columns": {},
            "generated_columns": [],
            "warnings": [],
            "has_usable_date": has_dates,
        }
        if loader_info:
            info.update(loader_info)
    else:
        normalized, info = normalize_dataframe(raw_df)
        if loader_info:
            info.update(loader_info)

    df = add_analysis(normalized)
    has_date = bool(info.get("has_usable_date", False) and ("date" in df.columns and df["date"].notna().sum() > 0))

    metadata = {
        "rows": len(df),
        "regions": int(df["region"].nunique()),
        "categories": int(df["category"].nunique()),
        "positive": int((df["sentiment"] == "Positive").sum()),
        "negative": int((df["sentiment"] == "Negative").sum()),
        "neutral": int((df["sentiment"] == "Neutral").sum()),
        "has_usable_date": has_date,
        "mapped_columns": info.get("mapped_columns", {}),
        "generated_columns": info.get("generated_columns", []),
        "warnings": info.get("warnings", []),
    }
    return df, metadata


def regional_metrics(df: pd.DataFrame, region: str, category: str):
    regional = df[df["region"] == region]
    match = regional[regional["category"] == category]
    frequency = round(len(match) / len(regional) * 100, 1) if len(regional) else 0.0
    negative = round((match["sentiment"] == "Negative").mean() * 100, 1) if len(match) else 0.0

    has_valid_dates = False
    trend = 0.0
    monthly = pd.Series(dtype=float)

    if len(match) and "date" in match.columns:
        valid_dates = match.dropna(subset=["date"])
        if len(valid_dates) > 0:
            try:
                dates = pd.to_datetime(valid_dates["date"], errors="coerce").dropna()
                if len(dates) > 0:
                    ts_series = pd.Series(1, index=dates)
                    monthly = ts_series.resample("MS").sum()
                    if len(monthly) >= 2:
                        trend = float(monthly.iloc[-1] - monthly.iloc[-2])
                    has_valid_dates = True
            except Exception:
                monthly = pd.Series(dtype=float)
                trend = 0.0

    sev = severity(frequency, negative)
    return {
        "regional": regional,
        "match": match,
        "frequency": frequency,
        "negative": negative,
        "monthly": monthly,
        "trend": trend,
        "has_usable_date": has_valid_dates,
        "severity": sev,
        "priority": priority_score(frequency, negative, sev, trend),
    }
