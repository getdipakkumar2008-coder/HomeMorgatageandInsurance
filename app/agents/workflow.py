"""LangGraph workflow graph — stateful orchestration of the recommendation pipeline."""
import logging
import uuid
from typing import Any, Dict, Optional

from langgraph.graph import END, START, StateGraph

from app.agents.nodes import (
    evaluate_confidence_node,
    fallback_risk_defaults,
    finalize_output,
    generate_explanation,
    human_review_gate,
    normalize_input,
    recommend_plan,
    score_risk,
    validate_input,
)
from app.agents.state import WorkflowState
from app.core.logging_config import get_logger

logger = get_logger(__name__)


def _should_use_fallback(state: WorkflowState) -> str:
    """Route to fallback risk defaults if enrichment failed."""
    if state.get("enrichment_failed", False):
        logger.warning("Enrichment failed — routing to fallback defaults")
        return "fallback"
    return "score"


def _should_human_review(state: WorkflowState) -> str:
    """Route to human review gate if confidence is below threshold."""
    if state.get("requires_human_review", False):
        return "review"
    return "finalize"


def _has_errors(state: WorkflowState) -> str:
    """Check if critical errors block further processing."""
    errors = state.get("errors", [])
    if errors:
        return "error"
    return "continue"


def build_workflow() -> StateGraph:
    """Construct and compile the LangGraph recommendation workflow."""
    graph = StateGraph(WorkflowState)

    # Add all nodes
    graph.add_node("validate_input", validate_input)
    graph.add_node("normalize_input", normalize_input)
    graph.add_node("enrich_risk", _enrich_risk_node)
    graph.add_node("fallback_risk_defaults", fallback_risk_defaults)
    graph.add_node("score_risk", score_risk)
    graph.add_node("recommend_plan", recommend_plan)
    graph.add_node("generate_explanation", generate_explanation)
    graph.add_node("evaluate_confidence", evaluate_confidence_node)
    graph.add_node("human_review_gate", human_review_gate)
    graph.add_node("finalize_output", finalize_output)

    # Entry point
    graph.add_edge(START, "validate_input")
    graph.add_edge("validate_input", "normalize_input")
    graph.add_edge("normalize_input", "enrich_risk")

    # Conditional: enrichment success or fallback
    graph.add_conditional_edges(
        "enrich_risk",
        _should_use_fallback,
        {"fallback": "fallback_risk_defaults", "score": "score_risk"},
    )
    graph.add_edge("fallback_risk_defaults", "score_risk")
    graph.add_edge("score_risk", "recommend_plan")
    graph.add_edge("recommend_plan", "evaluate_confidence")
    graph.add_edge("evaluate_confidence", "generate_explanation")

    # Conditional: human review or finalize
    graph.add_conditional_edges(
        "generate_explanation",
        _should_human_review,
        {"review": "human_review_gate", "finalize": "finalize_output"},
    )
    graph.add_edge("human_review_gate", "finalize_output")
    graph.add_edge("finalize_output", END)

    return graph


def _enrich_risk_node(state: WorkflowState) -> WorkflowState:
    """Wrap enrich_risk to keep import at module level."""
    from app.agents.nodes import enrich_risk

    return enrich_risk(state)


# Compile once at module level
_compiled_workflow = None


def get_compiled_workflow():
    """Return the compiled (cached) workflow graph."""
    global _compiled_workflow
    if _compiled_workflow is None:
        graph = build_workflow()
        _compiled_workflow = graph.compile()
        logger.info("LangGraph workflow compiled successfully")
    return _compiled_workflow


def run_recommendation_workflow(
    input_profile: Dict[str, Any],
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Execute the full recommendation workflow for a given input profile.

    Args:
        input_profile: Raw property and preference data dict
        request_id: Optional UUID string; generated if not provided

    Returns:
        Final output dict from the workflow
    """
    if request_id is None:
        request_id = str(uuid.uuid4())

    logger.info("Starting recommendation workflow | request_id=%s", request_id)

    initial_state: WorkflowState = {
        "input_profile": input_profile,
        "request_id": request_id,
        "errors": [],
        "trace_metadata": {"request_id": request_id},
    }

    workflow = get_compiled_workflow()
    final_state = workflow.invoke(initial_state)

    output = final_state.get("output", {})
    if not output:
        logger.error("Workflow produced no output | request_id=%s | errors=%s", request_id, final_state.get("errors"))
        output = {
            "request_id": request_id,
            "errors": final_state.get("errors", ["Unknown workflow failure"]),
        }

    return output
