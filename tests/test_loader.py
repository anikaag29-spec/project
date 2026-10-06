import hashlib
import pytest
import pandas as pd

from reviewlens.data_loader import (
    load_uploaded_csv,
    normalize_dataframe,
    _detect_delimiter,
    _infer_category,
    make_demo_data,
)


class FakeUpload:
    def __init__(self, text, name="reviews.csv", encoding="utf-8"):
        self.name = name
        if isinstance(text, bytes):
            self._bytes = text
        else:
            self._bytes = text.encode(encoding)

    def getvalue(self):
        return self._bytes


def test_standard_csv_loading():
    upload = FakeUpload(
        "review_id,review_text,region,category,rating,date\n"
        "REV-01,Fast delivery,Noida,Delivery,5,2026-02-01\n"
        "REV-02,Slow support,Delhi,Support,1,2026-02-02\n"
    )
    result = load_uploaded_csv(upload)
    assert len(result.data) == 2
    assert list(result.data["region"]) == ["Noida", "Delhi"]
    assert list(result.data["category"]) == ["Delivery", "Support"]


def test_column_alias_detection():
    upload = FakeUpload(
        "customer_feedback,City,Topic,Stars,Review Date,UUID\n"
        "Very fast delivery,Noida,Delivery,5,2026-01-02,UID-1\n"
        "Too expensive,Delhi,Price,2,2026-01-03,UID-2\n"
    )
    result = load_uploaded_csv(upload)
    assert len(result.data) == 2
    assert {"review_text", "region", "category", "rating", "date", "review_id"}.issubset(result.data.columns)
    assert result.data["review_text"].iloc[0] == "Very fast delivery"
    assert result.data["region"].iloc[0] == "Noida"


def test_encoding_detection_utf8_bom():
    raw = "\ufeffreview_text,region\nGreat quality,Noida\n".encode("utf-8-sig")
    upload = FakeUpload(raw, encoding="utf-8-sig")
    result = load_uploaded_csv(upload)
    assert len(result.data) == 1
    assert "review_text" in result.data.columns
    assert result.data["region"].iloc[0] == "Noida"


def test_encoding_detection_cp1252():
    # CP1252 specific byte sequence: \x80 is Euro sign in cp1252
    raw = b"review_text,region\nService is costly \x80,Mumbai\n"
    upload = FakeUpload(raw)
    result = load_uploaded_csv(upload)
    assert len(result.data) == 1
    assert "Mumbai" in list(result.data["region"])


@pytest.mark.parametrize("sep", [",", ";", "\t", "|"])
def test_delimiter_detection(sep):
    content = f"review_text{sep}region{sep}rating\nGreat product{sep}Pune{sep}5\nBad experience{sep}Goa{sep}1\n"
    upload = FakeUpload(content)
    result = load_uploaded_csv(upload)
    assert len(result.data) == 2
    assert result.data["region"].iloc[0] == "Pune"


def test_category_inference():
    # Test each category keyword
    assert _infer_category("The delivery courier arrived late") == "Delivery"
    assert _infer_category("The price was too expensive and high fee") == "Price"
    assert _infer_category("The product quality was broken and defective") == "Product Quality"
    assert _infer_category("Customer support agent was rude and unhelpful") == "Support"
    assert _infer_category("The mobile app website checkout screen had a bug") == "UX"
    assert _infer_category("Random completely unrelated chatter") == "Other"

    # Ensure no substring false positives (e.g. happy matching app, coffee matching fee)
    assert _infer_category("Really happy with everything") == "Other"
    assert _infer_category("Had a nice coffee during the meeting") == "Other"


def test_missing_optional_fields_are_generated():
    df = pd.DataFrame({"text": ["Great product", "Bad support"]})
    normalized, info = normalize_dataframe(df)
    assert len(normalized) == 2
    assert {"review_text", "region", "category", "rating", "date", "review_id"}.issubset(normalized.columns)
    assert all(normalized["region"] == "Unknown")
    assert info["has_usable_date"] is False


def test_missing_required_review_text_raises_error():
    upload = FakeUpload("score,city\n5,Noida\n1,Delhi\n")
    with pytest.raises(ValueError, match="ReviewLens requires a customer-feedback text field"):
        load_uploaded_csv(upload)


def test_all_empty_review_text_raises_error():
    upload = FakeUpload("review_text,region\n   ,Noida\n   ,Delhi\n")
    with pytest.raises(ValueError, match="empty review text"):
        load_uploaded_csv(upload)


def test_camel_case_alias_customer_review():
    upload = FakeUpload(
        "CustomerReview,City,Rating\n"
        "Delivery was quick and nice,Noida,5\n"
        "Slow customer support,Delhi,1\n"
    )
    result = load_uploaded_csv(upload)
    assert len(result.data) == 2
    assert "review_text" in result.data.columns
    assert result.data["review_text"].iloc[0] == "Delivery was quick and nice"


def test_hyphenated_alias_customer_review():
    upload = FakeUpload(
        "customer-review,city,rating,date\n"
        "Packaging was intact and fast shipping,Mumbai,5,2026-03-01\n"
    )
    result = load_uploaded_csv(upload)
    assert len(result.data) == 1
    assert result.data["review_text"].iloc[0] == "Packaging was intact and fast shipping"


def test_description_with_genuine_reviews_is_mapped():
    upload = FakeUpload(
        "description,location,rating\n"
        "The delivery was late and the packaging was damaged.,Noida,1\n"
        "Great customer service and very helpful support agent.,Gurgaon,5\n"
    )
    result = load_uploaded_csv(upload)
    assert len(result.data) == 2
    assert "review_text" in result.data.columns
    assert "Mapped 'description' to review text automatically." in result.metadata.warnings


def test_transactional_dataset_is_rejected_cleanly():
    upload = FakeUpload(
        "product_id,product_name,price,quantity,city,order_date\n"
        "101,Nike Pegasus 38,120,1,Noida,2026-01-01\n"
        "102,Apple iPhone 15,999,1,Delhi,2026-01-02\n",
        name="ecommerce_data.csv",
    )
    with pytest.raises(ValueError) as exc_info:
        load_uploaded_csv(upload)
    msg = str(exc_info.value)
    assert "ReviewLens requires a customer-feedback text field" in msg
    assert "product_id" in msg
    assert "product_name" in msg
    assert "city" in msg
    assert "transactional rather than review-based" in msg


def test_empty_csv_raises_error():
    upload = FakeUpload("")
    with pytest.raises(ValueError, match="empty"):
        load_uploaded_csv(upload)


def test_header_only_csv_raises_error():
    upload = FakeUpload("review_text,region,category\n")
    with pytest.raises(ValueError, match="no data rows"):
        load_uploaded_csv(upload)


def test_duplicate_rows_are_deduplicated():
    upload = FakeUpload(
        "review_text,region,category,rating\n"
        "Late package,Noida,Delivery,1\n"
        "Late package,Noida,Delivery,1\n"
        "Great item,Delhi,Product Quality,5\n"
    )
    result = load_uploaded_csv(upload)
    assert len(result.data) == 2
    assert any("duplicate" in w.lower() for w in result.metadata.warnings)


def test_same_filename_with_different_contents_signature():
    # Demonstrating the content hash signature behavior
    upload1 = FakeUpload("review_text,region\nGood,Noida\n", name="reviews.csv")
    upload2 = FakeUpload("review_text,region\nBad,Gurgaon\n", name="reviews.csv")

    sig1 = f"{upload1.name}:{hashlib.sha256(upload1.getvalue()).hexdigest()}"
    sig2 = f"{upload2.name}:{hashlib.sha256(upload2.getvalue()).hexdigest()}"

    assert upload1.name == upload2.name
    assert sig1 != sig2

