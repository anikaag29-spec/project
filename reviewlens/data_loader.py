from __future__ import annotations

import csv
import io
import re

import numpy as np
import pandas as pd

from .config import CATEGORIES, COLUMN_ALIASES
from .schemas import DatasetMetadata, LoadResult


def _canonical(value: object) -> str:
    val_str = str(value).strip()
    val_str = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", val_str)
    val_str = re.sub(r"[^a-z0-9]+", " ", val_str.lower()).strip()
    return re.sub(r"\s+", " ", val_str)


def _detect_delimiter(text: str) -> str:
    lines = [line for line in text.splitlines() if line.strip()][:30]
    if not lines:
        return ","

    try:
        sample = "\n".join(lines[:10])
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        if dialect.delimiter in (",", ";", "\t", "|"):
            if len(lines[0].split(dialect.delimiter)) >= 2:
                return dialect.delimiter
    except Exception:
        pass

    candidates = [",", ";", "\t", "|"]
    best_delim = ","
    best_score = -1.0
    for d in candidates:
        counts = [line.count(d) for line in lines]
        if max(counts) == 0:
            continue
        header_count = counts[0]
        if header_count > 0:
            consistent_lines = sum(1 for c in counts if c == header_count)
            score = (consistent_lines / len(counts)) * 100 + header_count
            if score > best_score:
                best_score = score
                best_delim = d

    return best_delim


def _read_csv(uploaded_file) -> pd.DataFrame:
    raw = uploaded_file.getvalue()
    if not raw or not raw.strip():
        raise ValueError("The uploaded CSV is empty.")

    text = None
    last_error = None
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin1", "iso-8859-1"):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError as exc:
            last_error = exc
    if text is None:
        raise ValueError(f"Could not decode the CSV. Supported encodings are UTF-8, CP1252 and Latin-1. {last_error}")

    separator = _detect_delimiter(text)

    try:
        df = pd.read_csv(
            io.StringIO(text),
            sep=separator,
            engine="python",
            on_bad_lines="warn",
            skip_blank_lines=True,
        )
    except Exception as exc:
        raise ValueError(
            "ReviewLens could not parse this CSV. Check that it has a header row and consistent delimiters."
        ) from exc

    df.columns = [str(c).strip().lstrip("\ufeff") for c in df.columns]
    df = df.dropna(how="all")

    if df.empty or len(df) == 0:
        raise ValueError("The uploaded CSV contains no data rows.")
    return df


def _find_column(columns, aliases, used_columns=None):
    used = set(used_columns or [])
    col_map = {}
    for c in columns:
        if c not in used:
            col_map[_canonical(c)] = c

    for alias in aliases:
        key = _canonical(alias)
        if key in col_map:
            return col_map[key]
    return None


PROSE_STOPWORDS = {
    "the", "and", "was", "is", "it", "to", "i", "my", "for", "in",
    "with", "not", "but", "of", "a", "an", "on", "that", "this",
    "so", "very", "at", "had", "have", "we", "they", "too", "you",
    "be", "as", "are", "from", "me", "all", "our", "just", "no",
    "if", "or", "when", "there", "their", "up", "out",
}

FEEDBACK_VOCABULARY = {
    "good", "great", "bad", "poor", "terrible", "worst", "best",
    "slow", "fast", "late", "delay", "delayed", "delays", "problem",
    "issue", "issues", "love", "loved", "happy", "disappoint",
    "disappointed", "disappointing", "damaged", "broken", "faulty",
    "defect", "defective", "excellent", "amazing", "horrible", "refund",
    "cheap", "expensive", "quality", "service", "support", "delivery",
    "experience", "recommend", "helpful", "unhelpful", "easy", "difficult",
    "worth", "waste", "ordered", "order", "orders", "received", "arrived",
    "package", "item", "product", "price", "cost", "money", "charged",
    "fee", "fees", "call", "agent", "app", "website", "bug", "glitch",
    "crash", "crashed", "crashes", "screen", "checkout", "rude", "nice",
    "fine", "ok", "okay", "response", "replied", "complaint", "satisfaction",
}

NON_REVIEW_NAME_TERMS = {
    "id", "uuid", "uid", "sku", "code", "price", "cost", "amount",
    "qty", "quantity", "city", "state", "country", "region", "zip",
    "postal", "date", "time", "timestamp", "year", "month", "status",
    "category", "rating", "stars", "score", "product", "product_name",
    "product name", "item", "item_name", "item name", "customer_name",
    "customer name", "user_name", "user name", "name", "phone", "email",
    "url", "order", "order_id", "order id", "transaction", "transaction_id",
    "transaction id", "address", "discount", "tax", "shipping_fee",
    "payment", "payment_method", "sales", "revenue", "profit",
}


def _is_explicit_review_name(col_name: str) -> bool:
    canon = _canonical(col_name)
    for bad in ["id", "date", "time", "rating", "score", "count", "num", "price", "qty", "code"]:
        if canon == bad or canon.endswith(f" {bad}") or canon.startswith(f"{bad} "):
            return False
    explicit_terms = {
        "review text", "review", "reviews", "customer review",
        "review content", "review body", "customer feedback",
        "user feedback", "customer comment", "comment", "comments",
        "feedback", "text", "reviewtext", "customerreview", "reviewcontent",
        "reviewbody", "customerfeedback", "userfeedback", "customercomment",
    }
    if canon in explicit_terms:
        return True
    words = canon.split()
    if any(w in ("review", "reviews", "feedback") for w in words):
        return True
    return False


def _evaluate_natural_language_column(series: pd.Series, col_name: str) -> tuple[float, bool]:
    canon = _canonical(col_name)
    for term in NON_REVIEW_NAME_TERMS:
        if canon == term or canon.endswith(f" {term}") or canon.startswith(f"{term} "):
            return -100.0, False

    non_empty = series.dropna().astype(str).str.strip()
    non_empty = non_empty[non_empty != ""]
    if len(non_empty) == 0:
        return -100.0, False

    fill_ratio = len(non_empty) / len(series)
    if fill_ratio < 0.2:
        return -100.0, False

    sample = non_empty.head(100).tolist()
    n = len(sample)

    word_counts = [len(s.split()) for s in sample]
    avg_words = sum(word_counts) / n
    avg_chars = sum(len(s) for s in sample) / n
    unique_count = len(set(sample))
    unique_ratio = unique_count / n

    if n >= 8 and unique_ratio < 0.25:
        return -100.0, False

    if avg_words < 1.8 and avg_chars < 15:
        return -100.0, False

    prose_hits = sum(1 for s in sample if any(w in PROSE_STOPWORDS for w in re.findall(r"\b[a-z]{1,10}\b", s.lower())))
    prose_ratio = prose_hits / n

    multi_prose_hits = sum(1 for s in sample if sum(1 for w in re.findall(r"\b[a-z]{1,10}\b", s.lower()) if w in PROSE_STOPWORDS) >= 2)
    multi_prose_ratio = multi_prose_hits / n

    feedback_hits = sum(1 for s in sample if any(w in FEEDBACK_VOCABULARY for w in re.findall(r"\b[a-z]{3,15}\b", s.lower())))
    feedback_ratio = feedback_hits / n

    punct_hits = sum(1 for s in sample if any(c in s for c in ".,!?;\"'"))
    punct_ratio = punct_hits / n

    name_score = 0.0
    if canon in {"description", "message", "remarks", "response", "opinion", "text", "body", "content", "notes", "details"}:
        name_score = 25.0
    elif any(k in canon for k in ["comment", "feedback", "review", "opinion", "remark", "response", "message", "experience", "note"]):
        name_score = 35.0

    content_score = (
        min(avg_words * 3.0, 30.0) +
        min(avg_chars * 0.3, 20.0) +
        (prose_ratio * 25.0) +
        (multi_prose_ratio * 20.0) +
        (feedback_ratio * 25.0) +
        (punct_ratio * 10.0) +
        (unique_ratio * 15.0)
    )

    total_score = name_score + content_score

    is_valid = False
    if avg_words >= 2.5 and (multi_prose_ratio >= 0.25 or (prose_ratio >= 0.4 and feedback_ratio >= 0.15)):
        is_valid = True
    elif avg_words >= 5.0 and prose_ratio >= 0.3:
        is_valid = True
    elif avg_chars >= 30.0 and (prose_ratio >= 0.3 or feedback_ratio >= 0.2):
        is_valid = True

    return total_score, is_valid


def _guess_text_column(df: pd.DataFrame, used_columns=None) -> str | None:
    used = set(used_columns or [])
    candidates = []
    for col in df.columns:
        if col in used:
            continue
        score, is_valid = _evaluate_natural_language_column(df[col], col)
        if is_valid and score > 40.0:
            candidates.append((score, col))
    if candidates:
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]
    return None


CATEGORY_PATTERNS = {
    "Delivery": [
        re.compile(r"\bdeliver(y|ed|ing|s)?\b", re.IGNORECASE),
        re.compile(r"\blate\b", re.IGNORECASE),
        re.compile(r"\bdelay(ed|s|ing)?\b", re.IGNORECASE),
        re.compile(r"\bshipping\b", re.IGNORECASE),
        re.compile(r"\bcourier\b", re.IGNORECASE),
        re.compile(r"\barriv(ed|al|e|ing)\b", re.IGNORECASE),
        re.compile(r"\btransit\b", re.IGNORECASE),
        re.compile(r"\bdispatch(ed)?\b", re.IGNORECASE),
        re.compile(r"\bparcel\b", re.IGNORECASE),
        re.compile(r"\bpackage\b", re.IGNORECASE),
    ],
    "Price": [
        re.compile(r"\bprice(s|d)?\b", re.IGNORECASE),
        re.compile(r"\bcost(s|ly|ing)?\b", re.IGNORECASE),
        re.compile(r"\bexpensive\b", re.IGNORECASE),
        re.compile(r"\bcheap\b", re.IGNORECASE),
        re.compile(r"\bdiscount(s)?\b", re.IGNORECASE),
        re.compile(r"\bcharge(s|d)?\b", re.IGNORECASE),
        re.compile(r"\bfee(s)?\b", re.IGNORECASE),
        re.compile(r"\boverpriced\b", re.IGNORECASE),
        re.compile(r"\bbilling\b", re.IGNORECASE),
        re.compile(r"\brefund(s|ed)?\b", re.IGNORECASE),
        re.compile(r"\bvalue\b", re.IGNORECASE),
    ],
    "Product Quality": [
        re.compile(r"\bquality\b", re.IGNORECASE),
        re.compile(r"\bbroken\b", re.IGNORECASE),
        re.compile(r"\bdamaged?\b", re.IGNORECASE),
        re.compile(r"\bdefect(ive|s)?\b", re.IGNORECASE),
        re.compile(r"\bproduct\b", re.IGNORECASE),
        re.compile(r"\bmaterial\b", re.IGNORECASE),
        re.compile(r"\bdurab(le|ility)\b", re.IGNORECASE),
        re.compile(r"\bfaulty\b", re.IGNORECASE),
        re.compile(r"\bitem\b", re.IGNORECASE),
        re.compile(r"\bauthentic\b", re.IGNORECASE),
        re.compile(r"\bbuild\b", re.IGNORECASE),
    ],
    "Support": [
        re.compile(r"\bsupport\b", re.IGNORECASE),
        re.compile(r"\bcustomer service\b", re.IGNORECASE),
        re.compile(r"\bcustomer care\b", re.IGNORECASE),
        re.compile(r"\bagent(s)?\b", re.IGNORECASE),
        re.compile(r"\bhelpdesk\b", re.IGNORECASE),
        re.compile(r"\bhelpline\b", re.IGNORECASE),
        re.compile(r"\bresponse\b", re.IGNORECASE),
        re.compile(r"\bunresolved\b", re.IGNORECASE),
        re.compile(r"\brude\b", re.IGNORECASE),
        re.compile(r"\brepresentative\b", re.IGNORECASE),
        re.compile(r"\bticket\b", re.IGNORECASE),
    ],
    "UX": [
        re.compile(r"\bapp\b", re.IGNORECASE),
        re.compile(r"\bwebsite\b", re.IGNORECASE),
        re.compile(r"\binterface\b", re.IGNORECASE),
        re.compile(r"\bui\b", re.IGNORECASE),
        re.compile(r"\bux\b", re.IGNORECASE),
        re.compile(r"\blogin\b", re.IGNORECASE),
        re.compile(r"\bcheckout\b", re.IGNORECASE),
        re.compile(r"\bconfusing\b", re.IGNORECASE),
        re.compile(r"\bnavigation\b", re.IGNORECASE),
        re.compile(r"\bcrash(es|ed)?\b", re.IGNORECASE),
        re.compile(r"\bglitch(es)?\b", re.IGNORECASE),
        re.compile(r"\bbug(s)?\b", re.IGNORECASE),
        re.compile(r"\bscreen\b", re.IGNORECASE),
        re.compile(r"\bbutton\b", re.IGNORECASE),
    ],
}


def _infer_category(text: str) -> str:
    text_str = str(text)
    scores = {}
    for name, patterns in CATEGORY_PATTERNS.items():
        score = sum(len(pat.findall(text_str)) for pat in patterns)
        scores[name] = score
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "Other"


def normalize_dataframe(df: pd.DataFrame):
    df = df.copy()
    mapped = {}
    generated = []
    warnings = []
    used_columns = set()

    orig_count = len(df)
    df = df.drop_duplicates()
    dup_removed = orig_count - len(df)
    if dup_removed > 0:
        warnings.append(f"Removed {dup_removed:,} duplicate row(s).")

    if df.empty:
        raise ValueError("The uploaded CSV contains no valid data rows.")

    review_source = None
    was_inferred = False

    for alias in COLUMN_ALIASES["review_text"]:
        matched = _find_column(df.columns, [alias], used_columns=used_columns)
        if matched and _is_explicit_review_name(matched):
            review_source = matched
            break

    if not review_source:
        guessed = _guess_text_column(df, used_columns=used_columns)
        if guessed:
            review_source = guessed
            was_inferred = True

    if not review_source:
        col_list = "\n".join(f"- {c}" for c in df.columns)
        raise ValueError(
            "ReviewLens requires a customer-feedback text field to perform complaint intelligence.\n\n"
            f"Detected columns:\n{col_list}\n\n"
            "This dataset appears to be transactional rather than review-based."
        )

    used_columns.add(review_source)
    if review_source != "review_text":
        mapped["review_text"] = review_source
        df = df.rename(columns={review_source: "review_text"})
    else:
        mapped["review_text"] = "review_text"

    if was_inferred:
        warnings.append(f"Mapped '{review_source}' to review text automatically.")

    for target in ["region", "category", "rating", "date", "review_id"]:
        aliases = COLUMN_ALIASES[target]
        source = _find_column(df.columns, aliases, used_columns=used_columns)
        if source:
            used_columns.add(source)
            if source != target:
                mapped[target] = source
                df = df.rename(columns={source: target})
            else:
                mapped[target] = target

    df["review_text"] = df["review_text"].fillna("").astype(str).str.strip()
    empty_text = int((df["review_text"] == "").sum())
    if empty_text == len(df):
        raise ValueError("All rows have empty review text. ReviewLens requires valid customer feedback.")
    if empty_text > 0:
        warnings.append(f"{empty_text} row(s) have empty review text.")

    if "region" not in df.columns:
        df["region"] = "Unknown"
        generated.append("region")
        warnings.append("No region column found; rows use 'Unknown'.")
    else:
        df["region"] = df["region"].fillna("Unknown").astype(str).str.strip().replace("", "Unknown")

    if "category" not in df.columns:
        df["category"] = df["review_text"].map(_infer_category)
        generated.append("category")
        warnings.append("No category column found; categories were inferred from review text.")
    else:
        known_map = {c.lower(): c for c in CATEGORIES}

        def _clean_cat(val, text):
            s = str(val).strip() if pd.notna(val) else ""
            if not s or s.lower() in ("unknown", "none", "nan", ""):
                return _infer_category(text)
            return known_map.get(s.lower(), s)

        df["category"] = [
            _clean_cat(c, t) for c, t in zip(df["category"], df["review_text"])
        ]

    if "rating" not in df.columns:
        df["rating"] = np.nan
        generated.append("rating")
    else:
        df["rating"] = pd.to_numeric(df["rating"], errors="coerce").clip(0, 5)

    has_usable_date = False
    if "date" not in df.columns:
        df["date"] = pd.NaT
        generated.append("date")
        warnings.append("No date column found; trend analysis is disabled.")
    else:
        parsed_dates = pd.to_datetime(df["date"], errors="coerce")
        valid_date_count = int(parsed_dates.notna().sum())
        if valid_date_count == 0:
            df["date"] = pd.NaT
            warnings.append("No valid dates found in date column; trend analysis is disabled.")
        else:
            df["date"] = parsed_dates
            has_usable_date = True
            if valid_date_count < len(df):
                warnings.append(f"{len(df) - valid_date_count} row(s) had unparseable dates.")

    if "review_id" not in df.columns:
        df["review_id"] = [f"REV-{i:06d}" for i in range(1, len(df) + 1)]
        generated.append("review_id")
    else:
        df["review_id"] = df["review_id"].fillna("").astype(str).str.strip()
        blank_ids = df["review_id"] == ""
        if blank_ids.any():
            df.loc[blank_ids, "review_id"] = [
                f"REV-{i:06d}" for i in range(1, int(blank_ids.sum()) + 1)
            ]

    canonical_cols = ["review_id", "review_text", "region", "category", "rating", "date"]
    other_cols = [c for c in df.columns if c not in canonical_cols]
    df = df[canonical_cols + other_cols]

    return df, {
        "mapped_columns": mapped,
        "generated_columns": generated,
        "warnings": warnings,
        "has_usable_date": has_usable_date,
    }


def load_uploaded_csv(uploaded_file) -> LoadResult:
    raw = _read_csv(uploaded_file)
    normalized, info = normalize_dataframe(raw)

    metadata = DatasetMetadata(
        source_name=getattr(uploaded_file, "name", "uploaded.csv"),
        rows=len(normalized),
        columns=list(normalized.columns),
        mapped_columns=info["mapped_columns"],
        generated_columns=info["generated_columns"],
        warnings=info["warnings"],
        has_usable_date=info.get("has_usable_date", False),
    )

    return LoadResult(
        data=normalized,
        message=f"Loaded {len(normalized):,} rows successfully.",
        metadata=metadata,
    )


def make_demo_data() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    rows = []
    sizes = {
        "Noida": 450, "Gurgaon": 450, "Delhi": 450, "Ghaziabad": 300,
        "Mumbai": 300, "Pune": 300, "Bengaluru": 300, "Hyderabad": 300,
        "Chennai": 300, "Kolkata": 300, "Ahmedabad": 250, "Jaipur": 250,
        "Lucknow": 250, "Chandigarh": 250, "Indore": 200, "Surat": 200,
    }
    positive = [
        "Fast delivery and good service.",
        "Really happy with the product.",
        "Excellent experience and easy to use.",
        "Great quality and quick support.",
        "Very smooth experience.",
    ]
    negative = [
        "Delivery was very late and frustrating.",
        "The price is too high for this product.",
        "Product quality was disappointing.",
        "Customer support did not resolve my issue.",
        "The app experience is confusing and slow.",
    ]
    neutral = [
        "The experience was okay.",
        "Product was acceptable.",
        "Delivery was average.",
        "Nothing special about the experience.",
        "It worked as expected.",
    ]

    other_categories = [c for c in CATEGORIES if c != "Delivery"]

    rid = 1
    for region, size in sizes.items():
        if region == "Noida":
            delivery_count = 144
        elif region == "Gurgaon":
            delivery_count = 90
        else:
            delivery_count = int(size * rng.uniform(0.18, 0.32))

        categories = ["Delivery"] * delivery_count
        non_delivery_count = size - delivery_count
        categories += [other_categories[i % len(other_categories)] for i in range(non_delivery_count)]
        rng.shuffle(categories)

        for category in categories:
            rating = int(rng.choice([1, 2, 3, 4, 5], p=[0.20, 0.25, 0.20, 0.20, 0.15]))
            idx = CATEGORIES.index(category)
            text = negative[idx % 5] if rating <= 2 else neutral[idx % 5] if rating == 3 else positive[idx % 5]
            date = pd.Timestamp(2026, 1, 1) + pd.Timedelta(days=int(rng.integers(0, 270)))
            rows.append({
                "review_id": f"REV-{rid:05d}",
                "review_text": text,
                "region": region,
                "category": category,
                "rating": rating,
                "date": date,
            })
            rid += 1

    return pd.DataFrame(rows)
