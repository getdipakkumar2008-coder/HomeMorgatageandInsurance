"""Core configuration module for HomeMortgageInsurance Planner."""
import logging
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "app" / "data"

logger = logging.getLogger(__name__)


class Settings:
    """Application settings loaded from environment variables."""

    # OpenAI
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # LangSmith
    langchain_tracing_v2: str = os.getenv("LANGCHAIN_TRACING_V2", "false")
    langchain_api_key: str = os.getenv("LANGCHAIN_API_KEY", "")
    langchain_project: str = os.getenv("LANGCHAIN_PROJECT", "hmip-planner")
    langchain_endpoint: str = os.getenv(
        "LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com"
    )

    # App
    app_name: str = "HomeMortgageInsurance Planner"
    app_version: str = "1.0.0"
    rules_version: str = "v1.0.0"
    catalog_version: str = "v1.0.0"
    prompt_version: str = "v1.0.0"
    risk_data_version: str = "v1.0.0"

    # Paths
    plan_catalog_path: Path = DATA_DIR / "plan_catalog.yaml"
    risk_factors_path: Path = DATA_DIR / "risk_factors.yaml"
    thresholds_path: Path = DATA_DIR / "thresholds.yaml"

    # Confidence
    low_confidence_threshold: float = float(
        os.getenv("LOW_CONFIDENCE_THRESHOLD", "0.60")
    )

    @property
    def has_openai_key(self) -> bool:
        return bool(self.openai_api_key)

    @property
    def tracing_enabled(self) -> bool:
        return self.langchain_tracing_v2.lower() == "true"


settings = Settings()
