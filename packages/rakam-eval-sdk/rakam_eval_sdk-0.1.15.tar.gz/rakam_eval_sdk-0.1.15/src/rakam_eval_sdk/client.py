import os
import random
from typing import Any, List, Optional, cast
import requests

from .schema import (
    EvalConfig,
    MetricConfig,
    SchemaEvalConfig,
    SchemaInputItem,
    SchemaMetricConfig,
    TextInputItem,
)


class DeepEvalClient:
    """
    Client for interacting with the DeepEval API.
    Provides synchronous and background evaluation with optional probability-based execution.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_token: Optional[str] = None,
        settings_module: Optional[Any] = None,  # optional external settings
        timeout: int = 30,
    ):
        settings_url = getattr(settings_module, "EVALFRAMWORK_URL", None)
        settings_token = getattr(settings_module, "EVALFRAMWORK_API_KEY", None)

        raw_url = (
            base_url
            or settings_url
            or os.getenv("EVALFRAMWORK_URL")
            or "http://localhost:8080"
        )
        self.base_url = raw_url.rstrip("/")
        self.api_token = (
            api_token or settings_token or os.getenv("EVALFRAMWORK_API_KEY", "")
        )
        self.timeout = timeout

    def _request(
        self,
        endpoint: str,
        payload: dict,
        raise_exception: bool = False,
    ) -> Optional[dict]:
        """Internal helper to send POST requests with standard headers and error handling."""
        url = f"{self.base_url}{endpoint}"
        headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
            "X-API-Token": self.api_token,
        }

        try:
            resp = requests.post(
                url, headers=headers, json=payload, timeout=self.timeout
            )
            if raise_exception:
                resp.raise_for_status()
        except requests.RequestException as e:
            if raise_exception:
                raise
            return {"error": str(e)}

        try:
            return cast(dict, resp.json())
        except ValueError:
            if raise_exception:
                raise
            return {"error": "Invalid JSON response", "raw": resp.text}

    def text_eval(
        self,
        data: List[TextInputItem],
        metrics: List[MetricConfig],
        raise_exception: bool = False,
        component: str = "unknown",
    ) -> Optional[dict]:
        """Run synchronous text evaluation."""
        payload = EvalConfig.model_construct(
            data=data, metrics=metrics, component=component
        ).model_dump()
        return self._request("/deepeval/text-eval", payload, raise_exception)

    def text_eval_background(
        self,
        data: List[TextInputItem],
        metrics: List[MetricConfig],
        raise_exception: bool = False,
        component: str = "unknown",
    ) -> Optional[dict]:
        """Run background text evaluation (async job)."""
        payload = EvalConfig.model_construct(
            data=data, metrics=metrics, component=component
        ).model_dump()
        return self._request("/deepeval/text-eval/background", payload, raise_exception)

    def schema_eval(
        self,
        data: List[SchemaInputItem],
        metrics: List[SchemaMetricConfig],
        raise_exception: bool = False,
        component: str = "unknown",
    ) -> Optional[dict]:
        """Run synchronous schema evaluation."""
        payload = SchemaEvalConfig.model_construct(
            data=data, metrics=metrics, component=component
        ).model_dump()
        return self._request("/deepeval/schema-eval", payload, raise_exception)

    def schema_eval_background(
        self,
        data: List[SchemaInputItem],
        metrics: List[SchemaMetricConfig],
        raise_exception: bool = False,
        component: str = "unknown",
    ) -> Optional[dict]:
        """Run background schema evaluation (async job)."""
        payload = SchemaEvalConfig.model_construct(
            data=data, metrics=metrics, component=component
        ).model_dump()
        return self._request(
            "/deepeval/schema-eval/background", payload, raise_exception
        )

    def maybe_text_eval(
        self,
        data: List[TextInputItem],
        metrics: List[MetricConfig],
        chance: float,
        raise_exception: bool = False,
        component: str = "unknown",
    ) -> Optional[dict]:
        """Randomly run text_eval based on a probability between 0 and 1."""
        self._validate_chance(chance)
        return (
            self.text_eval(data, metrics, raise_exception, component=component)
            if random.random() <= chance
            else None
        )

    def maybe_text_eval_background(
        self,
        data: List[TextInputItem],
        metrics: List[MetricConfig],
        chance: float,
        raise_exception: bool = False,
        component: str = "unknown",
    ) -> Optional[dict]:
        """Randomly run text_eval_background based on a probability between 0 and 1."""
        self._validate_chance(chance)
        return (
            self.text_eval_background(
                data, metrics, raise_exception, component=component
            )
            if random.random() <= chance
            else None
        )

    def maybe_schema_eval(
        self,
        data: List[SchemaInputItem],
        metrics: List[SchemaMetricConfig],
        chance: float,
        raise_exception: bool = False,
        component: str = "unknown",
    ) -> Optional[dict]:
        """Randomly run schema_eval based on a probability between 0 and 1."""
        self._validate_chance(chance)
        return (
            self.schema_eval(data, metrics, raise_exception, component=component)
            if random.random() <= chance
            else None
        )

    def maybe_schema_eval_background(
        self,
        data: List[SchemaInputItem],
        metrics: List[SchemaMetricConfig],
        chance: float,
        raise_exception: bool = False,
        component: str = "unknown",
    ) -> Optional[dict]:
        """Randomly run text_eval_background based on a probability between 0 and 1."""
        self._validate_chance(chance)
        return (
            self.schema_eval_background(
                data, metrics, raise_exception, component=component
            )
            if random.random() <= chance
            else None
        )

    @staticmethod
    def _validate_chance(chance: float) -> None:
        """Ensure chance is a valid probability between 0 and 1."""
        if not (0 <= chance <= 1):
            raise ValueError("chance must be between 0 and 1.")
