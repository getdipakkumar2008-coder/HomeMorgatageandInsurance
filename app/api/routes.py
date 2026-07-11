"""FastAPI REST API routes for HomeMortgageInsurance Planner."""
import logging
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from app.agents.workflow import run_recommendation_workflow
from app.core.config import settings
from app.core.logging_config import get_logger
from app.engine.rules import load_plan_catalog
from app.models.request import RecommendationRequest
from app.models.response import (
    ErrorResponse,
    PlanListResponse,
    RecommendationResponse,
    VersionInfo,
)

logger = get_logger(__name__)
router = APIRouter()


@router.post(
    "/v1/recommendation",
    response_model=RecommendationResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Generate insurance plan recommendation",
    description="Run the full recommendation pipeline for a property profile.",
)
async def create_recommendation(request: RecommendationRequest) -> RecommendationResponse:
    """Generate a home insurance recommendation for a given property profile."""
    logger.info(
        "POST /v1/recommendation | home_price=%.0f | zip=%s | state=%s",
        request.home_price,
        request.location_zip,
        request.state,
    )

    try:
        output = run_recommendation_workflow(request.model_dump())

        if "errors" in output and output["errors"] and not output.get("plan_tier"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Workflow errors: {'; '.join(output['errors'])}",
            )

        versions_data = output.get("versions", {})
        coverage = output.get("coverage_recommendation", {})

        from app.models.response import CoverageRecommendation

        response = RecommendationResponse(
            request_id=output.get("request_id", ""),
            plan_tier=output.get("plan_tier", "Standard"),
            coverage_recommendation=CoverageRecommendation(
                dwelling=coverage.get("dwelling", ""),
                personal_property=coverage.get("personal_property", ""),
                liability=coverage.get("liability", ""),
            ),
            premium_estimate_band=output.get("premium_estimate_band", ""),
            confidence_score=output.get("confidence_score", 1.0),
            reasons=output.get("reasons", []),
            explanation=output.get("explanation"),
            requires_human_review=output.get("requires_human_review", False),
            score_breakdown=output.get("score_breakdown", {}),
            trace_id=output.get("trace_id"),
            versions=VersionInfo(
                rules_version=versions_data.get("rules_version", settings.rules_version),
                catalog_version=versions_data.get("catalog_version", settings.catalog_version),
                prompt_version=versions_data.get("prompt_version", settings.prompt_version),
                risk_data_version=versions_data.get("risk_data_version", settings.risk_data_version),
            ),
        )
        return response

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Unexpected error in recommendation: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recommendation failed: {str(exc)}",
        )


@router.get(
    "/v1/plans",
    response_model=PlanListResponse,
    summary="List active insurance plans",
    description="Return the active plan catalog for transparency and UI display.",
)
async def list_plans() -> PlanListResponse:
    """Return the active plan catalog."""
    try:
        catalog = load_plan_catalog()
        plans_data: List[Dict[str, Any]] = [
            {
                "plan_id": p.plan_id,
                "plan_tier": p.plan_tier,
                "min_score": p.min_score,
                "max_score": p.max_score,
                "description": p.description,
                "features": p.features,
                "coverage_defaults": p.coverage_defaults.model_dump(),
            }
            for p in catalog.plans
        ]
        return PlanListResponse(
            catalog_version=catalog.catalog_version,
            plans=plans_data,
        )
    except Exception as exc:
        logger.error("Failed to load plan catalog: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load plan catalog: {str(exc)}",
        )


@router.get(
    "/v1/health",
    summary="Health check",
    description="Returns application health status.",
)
async def health_check() -> Dict[str, Any]:
    """Application health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
        "openai_configured": settings.has_openai_key,
        "tracing_enabled": settings.tracing_enabled,
    }
