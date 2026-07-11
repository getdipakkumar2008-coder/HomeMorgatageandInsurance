"""Explanation agent — LLM-powered rationale generation using LangChain."""
import logging
from typing import Any, Dict, Optional

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

_EXPLANATION_TEMPLATE = """You are a helpful home insurance advisor.

Based on the following property assessment, write a clear and friendly 2-3 paragraph explanation for why we recommend the {plan_tier} plan.

PROPERTY FACTS:
- Home Value: ${home_price:,.0f}
- Location: {city}, {state} ({zip_code})
- Property Type: {property_type}
- Year Built: {year_built}
- User Preference: {preference}

RISK ASSESSMENT:
- Geographic Hazard Score: {geo_hazard:.1f}/30 — {risk_flags_text}
- Value Exposure Score: {value_exposure:.1f}/30
- Property Condition Score: {property_condition:.1f}/20
- Affordability Alignment Score: {affordability:.1f}/20
- Total Risk Score: {total_score:.1f}/100

RECOMMENDATION: {plan_tier} plan
CONFIDENCE: {confidence:.0%}
PREMIUM ESTIMATE: {premium_band}

Write in plain English. Be transparent about the key risk drivers.
Do NOT make any legal guarantees, binding commitments, or underwriting decisions.
Do NOT change the recommended plan tier — it is final.
Keep the explanation concise and helpful."""


def generate_explanation(
    plan_tier: str,
    input_profile: Dict[str, Any],
    score_breakdown: Dict[str, float],
    risk_flags: list,
    confidence: float,
    premium_band: str,
) -> str:
    """
    Generate a user-friendly explanation using LangChain + ChatOpenAI.

    Falls back to a deterministic template explanation if LLM is unavailable.
    LLM output CANNOT override the plan tier — it only explains the decision.
    """
    if not settings.has_openai_key:
        logger.warning("No OpenAI API key — using template explanation fallback")
        return _build_fallback_explanation(
            plan_tier, input_profile, score_breakdown, risk_flags, confidence, premium_band
        )

    try:
        from langchain_core.output_parsers import StrOutputParser
        from langchain_core.prompts import PromptTemplate
        from langchain_openai import ChatOpenAI

        risk_flags_text = (
            ", ".join(risk_flags) if risk_flags else "No major hazard flags"
        )

        prompt = PromptTemplate.from_template(_EXPLANATION_TEMPLATE)
        llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0.3,
            api_key=settings.openai_api_key,
        )
        chain = prompt | llm | StrOutputParser()

        explanation = chain.invoke(
            {
                "plan_tier": plan_tier,
                "home_price": input_profile.get("home_price", 0),
                "city": input_profile.get("city", ""),
                "state": input_profile.get("state", ""),
                "zip_code": input_profile.get("location_zip", ""),
                "property_type": input_profile.get("property_type", ""),
                "year_built": input_profile.get("year_built", 0),
                "preference": input_profile.get("preference", "balanced"),
                "geo_hazard": score_breakdown.get("geo_hazard", 0),
                "value_exposure": score_breakdown.get("value_exposure", 0),
                "property_condition": score_breakdown.get("property_condition", 0),
                "affordability": score_breakdown.get("affordability_alignment", 0),
                "total_score": score_breakdown.get("total", 0),
                "risk_flags_text": risk_flags_text,
                "confidence": confidence,
                "premium_band": premium_band,
            }
        )
        logger.info("LLM explanation generated | plan=%s | length=%d", plan_tier, len(explanation))
        return explanation

    except Exception as exc:
        logger.error("LLM explanation failed: %s — using fallback", exc)
        return _build_fallback_explanation(
            plan_tier, input_profile, score_breakdown, risk_flags, confidence, premium_band
        )


def _build_fallback_explanation(
    plan_tier: str,
    input_profile: Dict[str, Any],
    score_breakdown: Dict[str, float],
    risk_flags: list,
    confidence: float,
    premium_band: str,
) -> str:
    """Build a deterministic fallback explanation when LLM is unavailable."""
    city = input_profile.get("city", "your area")
    state = input_profile.get("state", "")
    home_price = input_profile.get("home_price", 0)
    total = score_breakdown.get("total", 0)
    flags_text = (
        f"Notable risk factors include: {', '.join(risk_flags)}."
        if risk_flags
        else "No major regional hazard flags were identified."
    )

    return (
        f"Based on your property profile in {city}, {state}, our system recommends the "
        f"**{plan_tier}** insurance plan. Your property has an overall risk score of "
        f"{total:.0f}/100, which falls in the {plan_tier.lower()} tier range.\n\n"
        f"{flags_text} Your home value of ${home_price:,.0f} and property characteristics "
        f"have been factored into the coverage recommendation.\n\n"
        f"The estimated monthly premium for this plan is {premium_band}. "
        f"This recommendation was generated with {confidence:.0%} confidence. "
        f"Please consult with a licensed insurance agent to finalize your coverage."
    )
