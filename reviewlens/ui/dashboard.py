from __future__ import annotations

import streamlit as st
import pandas as pd

from ..analysis import regional_metrics


def metric_card(label, value, note=""):
    note_html = f'<div class="kpi-note">↑ {note}</div>' if note else ""
    st.markdown(
        f'<div class="metric-box">'
        f'<div class="lab">{label}</div>'
        f'<div class="num">{value}</div>'
        f'{note_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_dashboard(df, metadata, source_name, upload_message=None):
    total = len(df)
    pos = metadata.get("positive", 0)
    neg = metadata.get("negative", 0)
    pos_pct = round(pos / total * 100, 1) if total else 0
    neg_pct = round(neg / total * 100, 1) if total else 0

    brand_left, upload_col, status_col = st.columns([4.2, 3.0, 2.8])
    with brand_left:
        st.markdown(
            '<div class="brand-row">'
            '<div class="brand">'
            '<div class="logo">✦</div>'
            '<div>'
            '<div class="brand-name">ReviewLens AI</div>'
            '<div class="brand-sub">Regional customer intelligence / 2026</div>'
            '</div>'
            '</div>'
            '</div>',
            unsafe_allow_html=True,
        )
    with upload_col:
        st.write("")
        st.caption(upload_message or "Upload a customer-review CSV.")
    with status_col:
        st.markdown(
            f'<div class="status"><span class="status-dot"></span>{source_name} · <b>{total:,} reviews</b></div>',
            unsafe_allow_html=True,
        )

    if metadata.get("warnings") or metadata.get("mapped_columns") or metadata.get("generated_columns"):
        with st.expander("Dataset mapping & validation"):
            if metadata.get("mapped_columns"):
                st.write("Mapped columns:", metadata["mapped_columns"])
            if metadata.get("generated_columns"):
                st.write("Generated columns:", ", ".join(metadata["generated_columns"]))
            for warning in metadata.get("warnings", []):
                st.warning(warning)

    tabs = st.tabs(["01 / Overview", "02 / Regional Intelligence", "03 / Complaint Explorer", "04 / Trends", "05 / Evidence"])

    with tabs[0]:
        st.markdown('<div class="section-label">✦ Customer Complaint Intelligence</div>', unsafe_allow_html=True)
        st.markdown('<div class="hero-title">Find the problem.</div>', unsafe_allow_html=True)
        st.markdown('<div class="hero-sub">From overall volume to region, category, sentiment, severity, priority and customer evidence.</div>', unsafe_allow_html=True)

        a, b, c, d = st.columns(4)
        for col, (label, value, note) in zip(
            [a, b, c, d],
            [
                ("Total Reviews Analyzed", f"{total:,}", "parsed"),
                ("Positive Sentiment", f"{pos_pct}%", f"{pos:,} reviews"),
                ("Negative Sentiment", f"{neg_pct}%", f"{neg:,} reviews"),
                ("Regions / Categories", f'{metadata.get("regions", 0)} / {metadata.get("categories", 0)}', "detected"),
            ],
        ):
            with col:
                st.markdown(
                    f'<div class="kpi">'
                    f'<div class="kpi-label">{label}</div>'
                    f'<div class="kpi-value">{value}</div>'
                    f'<div class="kpi-note">↑ {note}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        st.write("")
        left, right = st.columns([1.35, 1])
        with left:
            with st.container(border=True):
                st.markdown('<div class="panel-title">Regional Signal</div><div class="panel-caption">Review volume by region</div>', unsafe_allow_html=True)
                rs = df.groupby("region").size().sort_values(ascending=False)
                st.bar_chart(rs, height=300, color="#FFD84D")
        with right:
            with st.container(border=True):
                st.markdown('<div class="panel-title">Complaint Categories</div><div class="panel-caption">Operational issue volume</div>', unsafe_allow_html=True)
                cs = df.groupby("category").size().sort_values(ascending=False)
                st.bar_chart(cs, height=300, color="#FFD84D")

        top_region = rs.index[0] if len(rs) else "Unknown"
        top_category = cs.index[0] if len(cs) else "Other"
        st.markdown('<div class="section-label">✦ Key Intelligence</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="insight"><div class="insight-title">📍 {top_region} has the largest review volume</div>'
            '<div class="insight-text">ReviewLens moves from overall volume into category, sentiment, severity and evidence.</div></div>'
            f'<div class="insight"><div class="insight-title">⚠️ {top_category} is the largest operational category</div>'
            '<div class="insight-text">Regional intelligence shows where the issue is concentrated instead of stopping at generic sentiment.</div></div>',
            unsafe_allow_html=True,
        )

    with tabs[1]:
        st.markdown('<div class="section-label">✦ Regional Complaint Intelligence</div>', unsafe_allow_html=True)
        st.markdown('<div class="hero-title">Where is the problem?</div>', unsafe_allow_html=True)
        st.markdown('<div class="hero-sub">Drill from region → category → sentiment → severity → priority → evidence.</div>', unsafe_allow_html=True)

        st.markdown(
            '<div class="hierarchy-bar">'
            '<span class="h-step active">REGION</span><span class="h-arrow">→</span>'
            '<span class="h-step active">CATEGORY</span><span class="h-arrow">→</span>'
            '<span class="h-step active">VOLUME</span><span class="h-arrow">→</span>'
            '<span class="h-step active">SENTIMENT</span><span class="h-arrow">→</span>'
            '<span class="h-step active">SEVERITY</span><span class="h-arrow">→</span>'
            '<span class="h-step active">PRIORITY</span><span class="h-arrow">→</span>'
            '<span class="h-step active">EVIDENCE</span>'
            '</div>',
            unsafe_allow_html=True,
        )

        r1, r2 = st.columns(2)
        with r1:
            selected_region = st.selectbox("1. Select Region", sorted(df.region.unique()), key="ri_region")
        with r2:
            selected_category = st.selectbox("2. Select Complaint Category", sorted(df.category.unique()), key="ri_cat")

        m = regional_metrics(df, selected_region, selected_category)

        # Region category distribution
        with st.container(border=True):
            st.markdown(f'<div class="panel-title">Category Distribution in {selected_region}</div><div class="panel-caption">Breakdown across all complaint categories in this region</div>', unsafe_allow_html=True)
            reg_cat_series = m["regional"].groupby("category").size().sort_values(ascending=False)
            st.bar_chart(reg_cat_series, height=200, color="#FFD84D")

        st.write("")
        q1, q2, q3, q4, q5 = st.columns(5)
        for col, (label, value) in zip(
            [q1, q2, q3, q4, q5],
            [
                ("Regional Reviews", f'{len(m["regional"]):,}'),
                ("Matching Reviews", f'{len(m["match"]):,}'),
                ("Complaint Share", f'{m["frequency"]}%'),
                ("Negative Polarity", f'{m["negative"]}%'),
                ("Priority", f'{m["priority"]}/100'),
            ],
        ):
            with col:
                metric_card(label, value)

        st.write("")
        x, y = st.columns(2)
        with x:
            badge = "badge-red" if m["severity"] == "HIGH" else "badge-yellow"
            st.markdown(
                f'<div class="metric-box"><div class="lab">SEVERITY</div>'
                f'<div style="margin-top:10px"><span class="badge {badge}">{m["severity"]}</span></div>'
                '<div class="lab" style="margin-top:16px; font-size:10px; opacity:0.85">Formula: 40% frequency + 30% negative polarity + 20% severity + 10% trend momentum</div></div>',
                unsafe_allow_html=True,
            )
        with y:
            trend_val = f'{m["trend"]:+.0f}' if m.get("has_usable_date") else "N/A"
            trend_note = "Change in matching reviews from previous month" if m.get("has_usable_date") else "No date data available in dataset"
            st.markdown(
                f'<div class="metric-box"><div class="lab">TREND MOMENTUM</div>'
                f'<div class="num">{trend_val}</div>'
                f'<div class="lab" style="font-size:10px; opacity:0.85">{trend_note}</div></div>',
                unsafe_allow_html=True,
            )

        st.write("")
        comp = df[df.category == selected_category].groupby("region").size().reset_index(name="reviews")
        totals = df.groupby("region").size().rename("regional_total")
        comp = comp.join(totals, on="region")
        comp["complaint_share_%"] = (comp.reviews / comp.regional_total * 100).round(1)
        comp = comp.sort_values("complaint_share_%", ascending=False)
        st.markdown('<div class="section-label">✦ Regional Comparison</div>', unsafe_allow_html=True)
        st.dataframe(
            comp.rename(columns={"region": "Region", "reviews": "Matching Reviews", "regional_total": "Regional Reviews", "complaint_share_%": "Complaint Share %"}),
            use_container_width=True, hide_index=True,
        )

        st.write("")
        st.markdown(f'<div class="section-label">✦ Supporting Evidence · {selected_region} / {selected_category}</div>', unsafe_allow_html=True)
        if len(m["match"]):
            reg_evidence = m["match"][["review_id", "review_text", "rating", "sentiment", "date"]].head(25)
            st.dataframe(reg_evidence, use_container_width=True, hide_index=True)
        else:
            st.info(f"No reviews found for {selected_region} in {selected_category}.")

    with tabs[2]:
        st.markdown('<div class="section-label">✦ Complaint Explorer</div>', unsafe_allow_html=True)
        st.markdown('<div class="hero-title">What are customers complaining about?</div>', unsafe_allow_html=True)
        st.markdown('<div class="hero-sub">Compare categories and identify where each issue is concentrated.</div>', unsafe_allow_html=True)

        summary = df.groupby("category").agg(
            reviews=("review_id", "count"),
            negative=("sentiment", lambda x: (x == "Negative").sum()),
            regions=("region", "nunique"),
        ).reset_index()
        summary["negative_%"] = (summary.negative / summary.reviews * 100).round(1)
        st.dataframe(
            summary.rename(columns={"category": "Category", "reviews": "Reviews", "negative": "Negative Reviews", "regions": "Regions Affected", "negative_%": "Negative %"}),
            use_container_width=True, hide_index=True,
        )

        selected = st.selectbox("Explore category", sorted(df.category.unique()), key="ce_cat")
        sub = df[df.category == selected]
        a, b, c = st.columns(3)
        for col, label, value in [
            (a, "Reviews", len(sub)),
            (b, "Negative %", round((sub.sentiment == "Negative").mean() * 100, 1) if len(sub) else 0),
            (c, "Regions Affected", sub.region.nunique()),
        ]:
            with col:
                metric_card(label, f'{value:,}{"%" if label == "Negative %" else ""}')
        with st.container(border=True):
            st.markdown(f'<div class="panel-title">{selected} by region</div>', unsafe_allow_html=True)
            st.bar_chart(sub.groupby("region").size().sort_values(ascending=False), height=320, color="#FFD84D")

    with tabs[3]:
        st.markdown('<div class="section-label">✦ Trends & Momentum</div>', unsafe_allow_html=True)
        st.markdown('<div class="hero-title">Is the problem improving?</div>', unsafe_allow_html=True)
        st.markdown('<div class="hero-sub">Trend calculations are derived from the uploaded dataset date field.</div>', unsafe_allow_html=True)

        has_dates = metadata.get("has_usable_date", False) and ("date" in df.columns and df["date"].notna().sum() > 0)
        if not has_dates:
            st.info("📅 Trend analysis is unavailable for this dataset because no valid date column was detected.")
        else:
            t1, t2 = st.columns(2)
            with t1:
                trend_region = st.selectbox("Region", ["All regions"] + sorted(df.region.unique()), key="tr_region")
            with t2:
                trend_category = st.selectbox("Category", ["All categories"] + sorted(df.category.unique()), key="tr_cat")

            td = df.dropna(subset=["date"]).copy()
            if trend_region != "All regions":
                td = td[td.region == trend_region]
            if trend_category != "All categories":
                td = td[td.category == trend_category]

            monthly = pd.Series(dtype=float)
            if len(td):
                try:
                    monthly = td.set_index("date").resample("MS").size().rename("reviews")
                except Exception:
                    monthly = pd.Series(dtype=float)

            if len(monthly):
                with st.container(border=True):
                    st.markdown('<div class="panel-title">Review volume trend</div>', unsafe_allow_html=True)
                    st.line_chart(monthly, height=330, color="#FFD84D")
                current = float(monthly.iloc[-1])
                previous = float(monthly.iloc[-2]) if len(monthly) > 1 else current
                change = current - previous
                change_pct = (change / previous * 100) if previous else 0.0
            else:
                current = previous = change = change_pct = 0.0

            a, b, c = st.columns(3)
            for col, label, value, note in [
                (a, "Current Period", f"{current:,.0f}", "latest month"),
                (b, "Previous Period", f"{previous:,.0f}", "prior month"),
                (c, "Change", f"{change:+,.0f}", f"{change_pct:+.1f}%"),
            ]:
                with col:
                    metric_card(label, value, note)

    with tabs[4]:
        st.markdown('<div class="section-label">✦ Evidence Layer</div>', unsafe_allow_html=True)
        st.markdown('<div class="hero-title">Show the customer evidence</div>', unsafe_allow_html=True)
        st.markdown('<div class="hero-sub">Every insight can be traced back to the underlying review text.</div>', unsafe_allow_html=True)

        e1, e2, e3 = st.columns(3)
        with e1:
            er = st.selectbox("Region", ["All regions"] + sorted(df.region.unique()), key="ev_region")
        with e2:
            ec = st.selectbox("Category", ["All categories"] + sorted(df.category.unique()), key="ev_cat")
        with e3:
            es = st.selectbox("Sentiment", ["All sentiments", "Negative", "Neutral", "Positive"], key="ev_sent")

        ev = df.copy()
        if er != "All regions":
            ev = ev[ev.region == er]
        if ec != "All categories":
            ev = ev[ev.category == ec]
        if es != "All sentiments":
            ev = ev[ev.sentiment == es]

        metric_card("Matching Evidence", f"{len(ev):,}", "customer reviews")
        if len(ev):
            sort_col = "date" if ("date" in ev.columns and ev["date"].notna().sum() > 0) else "review_id"
            display = ev[["review_id", "review_text", "region", "category", "rating", "sentiment", "date"]].sort_values(sort_col, ascending=False).head(100)
            st.dataframe(display, use_container_width=True, hide_index=True, height=480)
        else:
            st.info("No customer reviews match the selected filters.")

    st.markdown(
        '<div class="app-footer"><span>ReviewLens AI</span> · Regional Customer Review Intelligence · Production architecture</div>',
        unsafe_allow_html=True,
    )
