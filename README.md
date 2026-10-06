# ReviewLens AI — Production Architecture

A database-free, production-oriented customer review intelligence dashboard.

## Project structure

```text
ReviewLens-AI-Production/
├── app.py
├── requirements.txt
├── requirements-dev.txt
├── README.md
├── data/
│   └── sample_reviews.csv
├── tests/
│   └── test_loader.py
├── .streamlit/
│   └── config.toml
└── reviewlens/
    ├── config.py
    ├── schemas.py
    ├── data_loader.py
    ├── analysis.py
    └── ui/
        ├── styles.py
        └── dashboard.py
```

## Why CSV uploads work now

The previous monolithic implementation expected a narrow schema. This version has a dedicated ingestion layer.

It handles:

- UTF-8 / UTF-8 BOM / CP1252 / Latin-1
- comma, semicolon, tab and pipe delimiters
- common column aliases
- automatic review-text column detection
- missing region/category/date/rating/id recovery
- category inference from review text when category is absent
- invalid numeric ratings
- invalid dates
- empty rows / empty review text warnings
- clear errors instead of silently breaking the dashboard

Common aliases include:

`review_text` → `review`, `text`, `comment`, `feedback`

`region` → `city`, `location`, `area`

`category` → `topic`, `issue`, `type`

`rating` → `stars`, `score`

`date` → `review_date`, `created_at`, `timestamp`

`review_id` → `id`, `uuid`

## Backend

Python + Pandas + NumPy running in Streamlit.

There is intentionally no database. The uploaded CSV is normalized and analyzed in memory.

## Analysis pipeline

```text
Raw CSV
  ↓
CSV reader
  ↓
Schema mapping / recovery
  ↓
Normalized DataFrame
  ↓
Sentiment
  ↓
Region × Category metrics
  ↓
Severity
  ↓
Priority
  ↓
Date-derived trends
  ↓
Evidence
  ↓
Dashboard
```

## Run

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

## Test

```bash
pip install -r requirements-dev.txt
pytest -q
```

## Deployment

Streamlit Community Cloud:

- Main file: `app.py`
- Dependencies: `requirements.txt`
- No database or secrets required.

## AI-chat buttons

ReviewLens itself does not contain "Ask Google" or "Ask ChatGPT" actions. This project does not integrate those external chat actions.

## Production roadmap

For a commercial-scale deployment, keep this architecture and replace only the analysis implementation with a tested NLP service/model, add authentication, request logging, rate limiting and persistent object storage if required.
