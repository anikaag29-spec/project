from pathlib import Path
from streamlit.testing.v1 import AppTest

APP_PATH = str(Path(__file__).parent.parent / "app.py")


def test_app_initial_demo_dataset():
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()
    assert not at.exception
    assert at.session_state["source_name"] == "Demo dataset"


def test_app_upload_and_same_filename_reprocessing():
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()
    assert not at.exception

    # First upload: 3 rows with Noida
    csv1 = b"review_text,region,category,rating,date\nFast delivery 1,Noida,Delivery,5,2026-01-01\nFast delivery 2,Noida,Delivery,5,2026-01-02\nFast delivery 3,Noida,Delivery,5,2026-01-03\n"
    at.file_uploader[0].upload("custom_reviews.csv", csv1)
    at.run()
    assert not at.exception
    assert at.session_state["source_name"] == "custom_reviews.csv"
    assert len(at.session_state["raw_df"]) == 3
    assert at.session_state["raw_df"]["region"].iloc[0] == "Noida"

    # Second upload: Same filename "custom_reviews.csv", but 2 rows with Gurgaon
    csv2 = b"review_text,region,category,rating,date\nBad support 1,Gurgaon,Support,1,2026-01-01\nBad support 2,Gurgaon,Support,1,2026-01-02\n"
    at.file_uploader[0].upload("custom_reviews.csv", csv2)
    at.run()
    assert not at.exception
    assert at.session_state["source_name"] == "custom_reviews.csv"
    assert len(at.session_state["raw_df"]) == 2
    assert at.session_state["raw_df"]["region"].iloc[0] == "Gurgaon"


def test_app_invalid_upload_preserves_active_dataset():
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()
    assert not at.exception
    assert at.session_state["source_name"] == "Demo dataset"

    # Upload invalid transactional dataset: ecommerce_data.csv
    ecommerce_csv = b"product_id,product_name,price,quantity,city,order_date\n1,Shoe,100,1,Noida,2026-01-01\n"
    at.file_uploader[0].upload("ecommerce_data.csv", ecommerce_csv)
    at.run()
    assert not at.exception

    # Verification: source_name MUST NOT be overwritten with ecommerce_data.csv!
    assert at.session_state["source_name"] == "Demo dataset"
    assert at.session_state["source_name"] != "ecommerce_data.csv"
    assert at.session_state["upload_error"] is not None
    assert at.session_state["upload_error"][0] == "ecommerce_data.csv"
    assert "ReviewLens requires a customer-feedback text field" in at.session_state["upload_error"][1]
    # Check that error is rendered in UI
    assert any("Upload rejected" in e.value for e in at.error)

    # Next upload a valid dataset
    valid_csv = b"customer_review,city,rating,date\nGreat service,Noida,5,2026-01-01\n"
    at.file_uploader[0].upload("valid_feedback.csv", valid_csv)
    at.run()
    assert not at.exception
    assert at.session_state["source_name"] == "valid_feedback.csv"
    assert len(at.session_state["raw_df"]) == 1
    assert at.session_state["upload_error"] is None

    # Re-upload invalid dataset: should preserve valid_feedback.csv as active
    at.file_uploader[0].upload("ecommerce_data.csv", ecommerce_csv)
    at.run()
    assert not at.exception
    assert at.session_state["source_name"] == "valid_feedback.csv"
    assert at.session_state["source_name"] != "ecommerce_data.csv"
    assert len(at.session_state["raw_df"]) == 1
    assert at.session_state["upload_error"][0] == "ecommerce_data.csv"
