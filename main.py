"""
HomeMortgageInsurance Planner — Streamlit UI Entry Point

Run with: streamlit run main.py
"""
import sys
from pathlib import Path

# Ensure project root is on the path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st

from app.agents.workflow import run_recommendation_workflow
from app.core.config import settings
from app.core.logging_config import setup_logging

setup_logging()

# ─── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="🏠 HomeMortgageInsurance Planner",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
        }
        .tier-badge {
            display: inline-block;
            padding: 8px 20px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 1.1rem;
        }
        .tier-basic    { background: #28a745; color: white; }
        .tier-standard { background: #007bff; color: white; }
        .tier-premium  { background: #fd7e14; color: white; }
        .tier-custom   { background: #dc3545; color: white; }
        .review-banner {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 12px 16px;
            border-radius: 4px;
            margin: 8px 0;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─── Header ───────────────────────────────────────────────────────────────────
st.title("🏠 HomeMortgageInsurance Planner")
st.caption(
    "Intelligent, explainable home insurance recommendations powered by AI · "
    f"Rules {settings.rules_version} · Catalog {settings.catalog_version}"
)
st.divider()

# ─── Sidebar — Input Form ─────────────────────────────────────────────────────
with st.sidebar:
    st.header("📋 Property Details")

    home_price = st.number_input(
        "Home Value ($)",
        min_value=50_000,
        max_value=10_000_000,
        value=450_000,
        step=10_000,
        format="%d",
        help="Estimated market value of your home in USD",
    )

    col1, col2 = st.columns(2)
    with col1:
        location_zip = st.text_input(
            "ZIP Code",
            value="78701",
            max_chars=10,
            help="5-digit property ZIP code",
        )
    with col2:
        state = st.text_input(
            "State",
            value="TX",
            max_chars=2,
            help="Two-letter state abbreviation",
        ).upper()

    city = st.text_input(
        "City",
        value="Austin",
        help="City where the property is located",
    )

    property_type = st.selectbox(
        "Property Type",
        options=["single_family", "condo", "townhouse", "multi_family", "manufactured"],
        index=0,
        format_func=lambda x: x.replace("_", " ").title(),
        help="Type of residential property",
    )

    year_built = st.number_input(
        "Year Built",
        min_value=1800,
        max_value=2025,
        value=2005,
        step=1,
        help="Year the property was constructed",
    )

    st.subheader("💰 Financial & Preference")

    ltv_enabled = st.checkbox("Include LTV Ratio", value=False)
    ltv: float | None = None
    if ltv_enabled:
        ltv = st.slider(
            "Loan-to-Value (LTV)",
            min_value=0.0,
            max_value=1.5,
            value=0.80,
            step=0.01,
            format="%.2f",
            help="Ratio of mortgage balance to home value",
        )

    preference = st.radio(
        "Coverage Preference",
        options=["low_premium", "balanced", "high_protection"],
        index=1,
        format_func=lambda x: {
            "low_premium": "💵 Low Premium",
            "balanced": "⚖️ Balanced",
            "high_protection": "🛡️ High Protection",
        }[x],
        help="Your priority between cost savings and coverage breadth",
    )

    st.divider()
    run_button = st.button(
        "🔍 Get Recommendation",
        type="primary",
        use_container_width=True,
    )

# ─── Main Area ────────────────────────────────────────────────────────────────
if not run_button:
    st.info(
        "👈 Fill in your property details in the sidebar and click "
        "**Get Recommendation** to get your personalized insurance plan."
    )

    st.subheader("📌 How It Works")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("**1. Input**\nEnter your property details and preferences")
    with col2:
        st.markdown("**2. Risk Analysis**\nWe score geographic hazards, value, condition, and affordability")
    with col3:
        st.markdown("**3. Plan Match**\nDeterministic rules map your score to the optimal tier")
    with col4:
        st.markdown("**4. Explanation**\nAI explains the recommendation in plain language")

else:
    # ─── Validate minimal inputs ──────────────────────────────────────────
    if not location_zip or len(location_zip.strip()) < 5:
        st.error("❌ Please enter a valid 5-digit ZIP code.")
        st.stop()
    if not state or len(state.strip()) != 2:
        st.error("❌ Please enter a valid 2-letter state abbreviation.")
        st.stop()
    if not city.strip():
        st.error("❌ Please enter a city name.")
        st.stop()

    # ─── Run workflow ─────────────────────────────────────────────────────
    with st.spinner("⚙️ Analyzing your property and generating recommendation…"):
        input_profile = {
            "home_price": float(home_price),
            "location_zip": location_zip.strip(),
            "city": city.strip(),
            "state": state.strip(),
            "property_type": property_type,
            "year_built": int(year_built),
            "ltv": ltv,
            "preference": preference,
        }

        try:
            result = run_recommendation_workflow(input_profile)
        except Exception as exc:
            st.error(f"❌ Recommendation engine error: {exc}")
            st.stop()

    # ─── Check for hard errors ────────────────────────────────────────────
    errors = result.get("errors", [])
    if errors and not result.get("plan_tier"):
        st.error("❌ The recommendation engine encountered errors:")
        for err in errors:
            st.code(err)
        st.stop()

    # ─── Plan Tier Banner ─────────────────────────────────────────────────
    tier = result.get("plan_tier", "Standard")
    tier_class = f"tier-{tier.lower()}"
    confidence = result.get("confidence_score", 0.0)
    human_review = result.get("requires_human_review", False)

    col_tier, col_conf, col_premium = st.columns([2, 1, 1])

    with col_tier:
        st.markdown(
            f'<div style="padding:16px; border-radius:12px; background:#f8f9fa;">'
            f'<p style="margin:0; font-size:0.85rem; color:#6c757d;">Recommended Plan</p>'
            f'<span class="tier-badge {tier_class}">{tier}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with col_conf:
        confidence_color = "#28a745" if confidence >= 0.80 else "#ffc107" if confidence >= 0.60 else "#dc3545"
        st.metric(
            label="Confidence Score",
            value=f"{confidence:.0%}",
            delta=None,
            help="How confident the system is in this recommendation",
        )

    with col_premium:
        st.metric(
            label="Est. Monthly Premium",
            value=result.get("premium_estimate_band", "—"),
            delta=None,
        )

    # ─── Human Review Warning ─────────────────────────────────────────────
    if human_review:
        st.markdown(
            '<div class="review-banner">⚠️ <strong>Human Review Recommended:</strong> '
            "This case has been flagged for manual review due to lower confidence. "
            "Please consult with a licensed insurance advisor.</div>",
            unsafe_allow_html=True,
        )

    st.divider()

    # ─── Coverage Details ─────────────────────────────────────────────────
    st.subheader("🏡 Coverage Recommendation")
    coverage = result.get("coverage_recommendation", {})
    c1, c2, c3 = st.columns(3)
    with c1:
        st.info(f"**Dwelling Coverage**\n\n{coverage.get('dwelling', '—')}")
    with c2:
        st.info(f"**Personal Property**\n\n{coverage.get('personal_property', '—')}")
    with c3:
        st.info(f"**Liability Protection**\n\n{coverage.get('liability', '—')}")

    # ─── Score Breakdown ──────────────────────────────────────────────────
    st.subheader("📊 Risk Score Breakdown")
    breakdown = result.get("score_breakdown", {})

    col_geo, col_val, col_cond, col_afford = st.columns(4)
    with col_geo:
        st.metric("Geo Hazard", f"{breakdown.get('geo_hazard', 0):.1f}/30")
    with col_val:
        st.metric("Value Exposure", f"{breakdown.get('value_exposure', 0):.1f}/30")
    with col_cond:
        st.metric("Property Condition", f"{breakdown.get('property_condition', 0):.1f}/20")
    with col_afford:
        st.metric("Affordability", f"{breakdown.get('affordability_alignment', 0):.1f}/20")

    total_score = breakdown.get("total", 0)
    st.progress(
        int(min(total_score, 100)),
        text=f"Total Risk Score: **{total_score:.0f} / 100**",
    )

    # ─── Reasons ──────────────────────────────────────────────────────────
    reasons = result.get("reasons", [])
    if reasons:
        st.subheader("🔍 Key Risk Factors")
        for reason in reasons:
            st.markdown(f"• {reason}")

    # ─── AI Explanation ───────────────────────────────────────────────────
    explanation = result.get("explanation", "")
    if explanation:
        st.subheader("💬 Advisor Explanation")
        st.markdown(explanation)

    # ─── Metadata ─────────────────────────────────────────────────────────
    with st.expander("🔧 Technical Details", expanded=False):
        versions = result.get("versions", {})
        st.json(
            {
                "request_id": result.get("request_id"),
                "trace_id": result.get("trace_id"),
                "versions": versions,
                "input_profile": input_profile,
            }
        )

    st.divider()
    st.caption(
        "⚠️ This recommendation is for informational purposes only and does not constitute "
        "a binding insurance quote or legal underwriting decision. "
        "Please consult a licensed insurance professional."
    )
