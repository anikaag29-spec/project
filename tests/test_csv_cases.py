import io
import pytest
import numpy as np
import pandas as pd

from reviewlens.data_loader import load_uploaded_csv
from reviewlens.analysis import analyze_reviews, regional_metrics


class MemoryUpload:
    def __init__(self, content, name="test.csv", encoding="utf-8"):
        self.name = name
        if isinstance(content, bytes):
            self._bytes = content
        else:
            self._bytes = content.encode(encoding)

    def getvalue(self):
        return self._bytes


def _run_pipeline(upload):
    result = load_uploaded_csv(upload)
    df, meta = analyze_reviews(result.data, assume_normalized=True, loader_info={
        "mapped_columns": result.metadata.mapped_columns,
        "generated_columns": result.metadata.generated_columns,
        "warnings": result.metadata.warnings,
        "has_usable_date": result.metadata.has_usable_date,
    })
    # Run regional metrics for each unique region/category to ensure no crash
    for r in df["region"].unique()[:2]:
        for c in df["category"].unique()[:2]:
            m = regional_metrics(df, r, c)
            assert "priority" in m
    return df, meta


# Case A: Standard CSV
def test_case_a_standard_csv():
    csv_data = (
        "review_text,region,category,rating,date,review_id\n"
        "Delivery was quick,Noida,Delivery,5,2026-03-01,REV-001\n"
        "Price is high,Delhi,Price,2,2026-03-02,REV-002\n"
    )
    df, meta = _run_pipeline(MemoryUpload(csv_data))
    assert len(df) == 2
    assert meta["has_usable_date"] is True


# Case B: Different column names
def test_case_b_different_column_names():
    csv_data = (
        "Review,City,Category,Rating,Date,ID\n"
        "Delivery was quick,Noida,Delivery,5,2026-03-01,101\n"
        "Price is high,Delhi,Price,2,2026-03-02,102\n"
    )
    df, meta = _run_pipeline(MemoryUpload(csv_data))
    assert len(df) == 2
    assert "review_text" in df.columns
    assert "region" in df.columns


# Case C: No category column
def test_case_c_no_category():
    csv_data = (
        "review_text,region,rating,date\n"
        "Delivery was late and delayed,Noida,1,2026-03-01\n"
        "The app crashed during checkout,Delhi,1,2026-03-02\n"
    )
    df, meta = _run_pipeline(MemoryUpload(csv_data))
    assert len(df) == 2
    assert set(df["category"]) == {"Delivery", "UX"}


# Case D: No rating
def test_case_d_no_rating():
    csv_data = (
        "review_text,region,category,date\n"
        "Great experience,Noida,Delivery,2026-03-01\n"
        "Terrible experience,Delhi,Price,2026-03-02\n"
    )
    df, meta = _run_pipeline(MemoryUpload(csv_data))
    assert len(df) == 2
    assert df["sentiment"].iloc[0] == "Positive"
    assert df["sentiment"].iloc[1] == "Negative"


# Case E: No date
def test_case_e_no_date():
    csv_data = (
        "review_text,region,category,rating\n"
        "Great delivery,Noida,Delivery,5\n"
        "Bad price,Delhi,Price,1\n"
    )
    df, meta = _run_pipeline(MemoryUpload(csv_data))
    assert len(df) == 2
    assert meta["has_usable_date"] is False


# Case F: Semicolon-delimited CSV
def test_case_f_semicolon_delimited():
    csv_data = (
        "review_text;region;category;rating;date\n"
        "Great delivery;Noida;Delivery;5;2026-03-01\n"
        "Bad price;Delhi;Price;1;2026-03-02\n"
    )
    df, meta = _run_pipeline(MemoryUpload(csv_data))
    assert len(df) == 2
    assert df["region"].iloc[0] == "Noida"


# Case G: Tab-delimited CSV
def test_case_g_tab_delimited():
    csv_data = (
        "review_text\tregion\tcategory\trating\tdate\n"
        "Great delivery\tNoida\tDelivery\t5\t2026-03-01\n"
        "Bad price\tDelhi\tPrice\t1\t2026-03-02\n"
    )
    df, meta = _run_pipeline(MemoryUpload(csv_data))
    assert len(df) == 2
    assert df["region"].iloc[0] == "Noida"


# Case H: Pipe-delimited CSV
def test_case_h_pipe_delimited():
    csv_data = (
        "review_text|region|category|rating|date\n"
        "Great delivery|Noida|Delivery|5|2026-03-01\n"
        "Bad price|Delhi|Price|1|2026-03-02\n"
    )
    df, meta = _run_pipeline(MemoryUpload(csv_data))
    assert len(df) == 2
    assert df["region"].iloc[0] == "Noida"


# Case I: UTF-8 CSV
def test_case_i_utf8():
    csv_data = (
        "review_text,region,category,rating,date\n"
        "Café delivery was super fast,Noida,Delivery,5,2026-03-01\n"
    )
    df, meta = _run_pipeline(MemoryUpload(csv_data.encode("utf-8")))
    assert len(df) == 1


# Case J: UTF-8 BOM CSV
def test_case_j_utf8_bom():
    csv_data = (
        "\ufeffreview_text,region,category,rating,date\n"
        "Fast delivery,Noida,Delivery,5,2026-03-01\n"
    )
    df, meta = _run_pipeline(MemoryUpload(csv_data.encode("utf-8-sig")))
    assert len(df) == 1
    assert "review_text" in df.columns


# Case K: Windows-1252 CSV
def test_case_k_windows_1252():
    csv_data = b"review_text,region,rating\nCost is 50 \x80,Noida,2\n"
    df, meta = _run_pipeline(MemoryUpload(csv_data))
    assert len(df) == 1


# Case L: CSV containing empty rows
def test_case_l_empty_rows():
    csv_data = (
        "review_text,region,rating\n"
        "\n"
        "Delivery was quick,Noida,5\n"
        "\n"
        "Price was too high,Delhi,1\n"
        "\n"
    )
    df, meta = _run_pipeline(MemoryUpload(csv_data))
    assert len(df) == 2


# Case M: CSV containing missing values
def test_case_m_missing_values():
    csv_data = (
        "review_text,region,category,rating,date\n"
        "Great delivery,,,5,\n"
        "Late package,Delhi,Delivery,,2026-03-02\n"
    )
    df, meta = _run_pipeline(MemoryUpload(csv_data))
    assert len(df) == 2
    assert df["region"].iloc[0] == "Unknown"
    assert df["category"].iloc[0] == "Delivery"


# Case N: CSV with extra unrelated columns
def test_case_n_extra_columns():
    csv_data = (
        "review_text,region,rating,sales_rep,discount_code,internal_notes\n"
        "Quick service,Noida,5,Alice,DISC10,VIP customer\n"
        "Broken box,Delhi,1,Bob,NONE,Inspect shipping\n"
    )
    df, meta = _run_pipeline(MemoryUpload(csv_data))
    assert len(df) == 2
    assert "sales_rep" in df.columns
    assert "internal_notes" in df.columns


# Case O: CSV with duplicate-looking column names
def test_case_o_duplicate_looking_columns():
    csv_data = (
        "review_text,Review,region,rating\n"
        "First text,Duplicate text,Noida,5\n"
    )
    df, meta = _run_pipeline(MemoryUpload(csv_data))
    assert len(df) == 1
    assert df["region"].iloc[0] == "Noida"


# Case P: CSV with large number of rows
def test_case_p_large_csv():
    lines = ["review_text,region,category,rating,date"]
    for i in range(5000):
        lines.append(f"Review number {i} with prompt delivery,City-{i % 10},Delivery,{1 + (i % 5)},2026-03-01")
    csv_data = "\n".join(lines)
    df, meta = _run_pipeline(MemoryUpload(csv_data))
    assert len(df) == 5000
    assert meta["rows"] == 5000


# Case Q: customer_review with city, rating, date
def test_case_q_customer_review():
    csv_data = (
        "customer_review,city,rating,date\n"
        "Delivery was late and delayed,Noida,1,2026-03-01\n"
        "Great quality product,Delhi,5,2026-03-02\n"
    )
    df, meta = _run_pipeline(MemoryUpload(csv_data))
    assert len(df) == 2
    assert "review_text" in df.columns
    assert df["review_text"].iloc[0] == "Delivery was late and delayed"


# Case R: Customer Review with spaces and camelCase tolerance
def test_case_r_customer_review_spaces():
    csv_data = (
        "Customer Review,City,Category,Rating,Date,ID\n"
        "Prompt service,Noida,Delivery,5,2026-03-01,101\n"
        "Expensive price,Delhi,Price,2,2026-03-02,102\n"
    )
    df, meta = _run_pipeline(MemoryUpload(csv_data))
    assert len(df) == 2
    assert "review_text" in df.columns
    assert "region" in df.columns


# Case S: description with genuine feedback
def test_case_s_description_with_genuine_feedback():
    csv_data = (
        "description,location,rating\n"
        "The delivery was late and the packaging was damaged.,Noida,1\n"
        "The customer service was great and very responsive.,Delhi,5\n"
    )
    df, meta = _run_pipeline(MemoryUpload(csv_data))
    assert len(df) == 2
    assert "review_text" in df.columns
    assert df["review_text"].iloc[0] == "The delivery was late and the packaging was damaged."


# Case T: Transactional ecommerce data rejection
def test_case_t_transactional_data_rejected():
    csv_data = (
        "product_id,product_name,price,quantity,city,order_date\n"
        "PRD-01,Running Shoes,120,2,Noida,2026-01-01\n"
        "PRD-02,Coffee Maker,80,1,Delhi,2026-01-02\n"
    )
    with pytest.raises(ValueError) as exc:
        _run_pipeline(MemoryUpload(csv_data, name="ecommerce_data.csv"))
    err = str(exc.value)
    assert "ReviewLens requires a customer-feedback text field" in err
    assert "product_id" in err
    assert "product_name" in err
    assert "city" in err
    assert "transactional rather than review-based" in err
