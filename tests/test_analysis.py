import pandas as pd
import pytest

from reviewlens.analysis import (
    get_sentiment,
    severity,
    priority_score,
    analyze_reviews,
    regional_metrics,
)
from reviewlens.data_loader import make_demo_data


def test_sentiment_calculation():
    # Rating-based sentiment
    assert get_sentiment({"review_text": "Good", "rating": 1}) == "Negative"
    assert get_sentiment({"review_text": "Average", "rating": 2}) == "Negative"
    assert get_sentiment({"review_text": "Average", "rating": 4}) == "Positive"
    assert get_sentiment({"review_text": "Bad", "rating": 5}) == "Positive"

    # Text-based sentiment when rating is NaN or neutral
    assert get_sentiment({"review_text": "Delivery was late and terrible", "rating": float("nan")}) == "Negative"
    assert get_sentiment({"review_text": "Amazing fast service loved it", "rating": float("nan")}) == "Positive"
    assert get_sentiment({"review_text": "Standard packaging", "rating": 3}) == "Neutral"


def test_severity_levels():
    assert severity(32.0, 50.0) == "HIGH"
    assert severity(10.0, 85.0) == "HIGH"
    assert severity(22.0, 40.0) == "MEDIUM"
    assert severity(15.0, 65.0) == "MEDIUM"
    assert severity(10.0, 20.0) == "LOW"


def test_regional_metrics_calculation():
    df = pd.DataFrame([
        {"review_id": "1", "review_text": "Late delivery", "region": "Noida", "category": "Delivery", "rating": 1, "sentiment": "Negative", "date": pd.Timestamp("2026-01-15")},
        {"review_id": "2", "review_text": "Late courier", "region": "Noida", "category": "Delivery", "rating": 1, "sentiment": "Negative", "date": pd.Timestamp("2026-02-15")},
        {"review_id": "3", "review_text": "Okay item", "region": "Noida", "category": "Product Quality", "rating": 3, "sentiment": "Neutral", "date": pd.Timestamp("2026-02-16")},
        {"review_id": "4", "review_text": "Good app", "region": "Delhi", "category": "UX", "rating": 5, "sentiment": "Positive", "date": pd.Timestamp("2026-02-17")},
    ])

    m = regional_metrics(df, "Noida", "Delivery")
    assert len(m["regional"]) == 3
    assert len(m["match"]) == 2
    assert m["frequency"] == round(2 / 3 * 100, 1)
    assert m["negative"] == 100.0
    assert m["severity"] == "HIGH"
    assert m["has_usable_date"] is True
    # Monthly resample: Jan = 1, Feb = 1. Trend = 1 - 1 = 0
    assert m["trend"] == 0.0


def test_regional_metrics_without_dates():
    df = pd.DataFrame([
        {"review_id": "1", "review_text": "Late", "region": "Noida", "category": "Delivery", "rating": 1, "sentiment": "Negative", "date": pd.NaT},
        {"review_id": "2", "review_text": "Slow", "region": "Noida", "category": "Delivery", "rating": 2, "sentiment": "Negative", "date": pd.NaT},
    ])
    m = regional_metrics(df, "Noida", "Delivery")
    assert m["has_usable_date"] is False
    assert m["trend"] == 0.0
    assert len(m["monthly"]) == 0


def test_analyze_reviews_pipeline():
    raw_df = pd.DataFrame({
        "review": ["Fast delivery", "Terrible price", "Broken product"],
        "city": ["Noida", "Delhi", "Mumbai"],
        "score": [5, 1, 2],
    })
    df, meta = analyze_reviews(raw_df)
    assert meta["rows"] == 3
    assert meta["regions"] == 3
    assert meta["positive"] == 1
    assert meta["negative"] == 2
    assert "sentiment" in df.columns


def test_demo_dataset_exact_requirements():
    df = make_demo_data()

    # 1. Total reviews = 4,850
    assert len(df) == 4850

    # 2. Noida: 144 delivery reviews out of 450 (32.0%)
    noida_df = df[df["region"] == "Noida"]
    assert len(noida_df) == 450
    noida_del = noida_df[noida_df["category"] == "Delivery"]
    assert len(noida_del) == 144
    assert round(len(noida_del) / len(noida_df) * 100, 1) == 32.0

    # 3. Gurgaon: 90 delivery reviews out of 450 (20.0%)
    gurgaon_df = df[df["region"] == "Gurgaon"]
    assert len(gurgaon_df) == 450
    gurgaon_del = gurgaon_df[gurgaon_df["category"] == "Delivery"]
    assert len(gurgaon_del) == 90
    assert round(len(gurgaon_del) / len(gurgaon_df) * 100, 1) == 20.0

    # 4. All 5 categories present
    assert set(df["category"].unique()) == {"Delivery", "Price", "Product Quality", "Support", "UX"}
