import hashlib

import streamlit as st

from reviewlens.config import APP_TITLE
from reviewlens.data_loader import load_uploaded_csv, make_demo_data
from reviewlens.analysis import analyze_reviews
from reviewlens.ui.styles import inject_styles
from reviewlens.ui.dashboard import render_dashboard

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_styles()

# Session state stores the already-normalized dataset. This avoids parsing and
# normalizing the same upload multiple times on every Streamlit rerun.
DEFAULT_STATE = {
    "raw_df": None,
    "source_name": "Demo dataset",
    "load_message": None,
    "loader_info": None,
    "uploaded_signature": None,
    "upload_error": None,
}
for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value

uploaded = st.file_uploader(
    "Upload CSV",
    type=["csv"],
    label_visibility="collapsed",
    help="Upload a customer-review CSV. ReviewLens automatically maps common column names.",
)

if uploaded is not None:
    # Use filename + SHA-256 of file bytes so any change in content triggers reprocessing
    # even when the uploaded file keeps the identical name.
    file_bytes = uploaded.getvalue()
    signature = f"{uploaded.name}:{hashlib.sha256(file_bytes).hexdigest()}"

    if st.session_state.uploaded_signature != signature:
        try:
            result = load_uploaded_csv(uploaded)
            st.session_state.raw_df = result.data
            st.session_state.source_name = uploaded.name
            st.session_state.uploaded_signature = signature
            st.session_state.load_message = result.message
            st.session_state.loader_info = {
                "mapped_columns": result.metadata.mapped_columns,
                "generated_columns": result.metadata.generated_columns,
                "warnings": result.metadata.warnings,
                "has_usable_date": result.metadata.has_usable_date,
            }
            st.session_state.upload_error = None
        except Exception as exc:
            # On validation failure, mark this signature so we don't repeat work on reruns,
            # but NEVER overwrite source_name or raw_df with the rejected file's details.
            st.session_state.uploaded_signature = signature
            st.session_state.upload_error = (uploaded.name, str(exc))
else:
    # When an upload is cleared by the user, gracefully revert to the demo dataset
    if st.session_state.uploaded_signature is not None:
        st.session_state.raw_df = None
        st.session_state.source_name = "Demo dataset"
        st.session_state.uploaded_signature = None
        st.session_state.load_message = None
        st.session_state.loader_info = None
        st.session_state.upload_error = None

if st.session_state.upload_error:
    err_filename, err_text = st.session_state.upload_error
    st.error(f"**Upload rejected:** `{err_filename}` could not be analyzed.\n\n{err_text}")
    st.info(f"Active dataset remains: **{st.session_state.source_name}**.")

# The demo data is already in canonical ReviewLens schema, so it can go
# directly into analysis without another ingestion pass.
if st.session_state.raw_df is None:
    raw_df = make_demo_data()
    df, metadata = analyze_reviews(raw_df, assume_normalized=True)
else:
    raw_df = st.session_state.raw_df.copy()
    df, metadata = analyze_reviews(
        raw_df,
        assume_normalized=True,
        loader_info=st.session_state.loader_info,
    )

render_dashboard(
    df=df,
    metadata=metadata,
    source_name=st.session_state.source_name,
    upload_message=st.session_state.load_message,
)
