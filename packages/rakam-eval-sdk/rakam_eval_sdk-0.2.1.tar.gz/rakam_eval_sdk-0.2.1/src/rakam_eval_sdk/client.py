import os
import random
from typing import Any, Dict, List, Optional, Union, cast, overload

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
        settings_url = getattr(settings_module, "EVALFRAMEWORK_URL", None)
        settings_token = getattr(settings_module, "EVALFRAMWORK_API_KEY", None)

        raw_url = (
            base_url
            or settings_url
            or os.getenv("EVALFRAMEWORK_URL")
            or "http://localhost:8080"
        )
        self.base_url = raw_url.rstrip("/")
        self.api_token = (
            api_token or settings_token or os.getenv(
                "EVALFRAMEWORK_API_KEY", "")
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

    def _get(
        self,
        endpoint: str,
        params: dict,
        raise_exception: bool = False,
    ) -> Optional[dict]:
        """Internal helper to send GET requests with standard headers and error handling."""
        url = f"{self.base_url}{endpoint}"
        headers = {
            "accept": "application/json",
            "X-API-Token": self.api_token,
        }

        try:
            resp = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=self.timeout,
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

    def list_evaluation_testcases(
        self,
        *,
        limit: int = 10,
        offset: int = 0,
        raise_exception: bool = False,
    ) -> Optional[List[Dict]]:
        """
        List evaluation testcases for the current API token only.
        Sorted by created_at DESC (newest first).
        """
        return self._get(
            "/eval-framework/deepeval/evaluation-testcases/token",
            params={
                "limit": limit,
                "offset": offset,
            },
            raise_exception=raise_exception,
        )

    def get_evaluation_testcase_by_id(
        self,
        testcase_id: int,
        *,
        raise_exception: bool = False,
    ) -> Optional[Dict]:
        """
        Fetch a single evaluation testcase by numeric ID.
        """
        return self._get(
            f"/eval-framework/deepeval/id/{testcase_id}",
            params={},
            raise_exception=raise_exception,
        )

    def get_evaluation_testcase_by_unique_id(
        self,
        unique_id: str,
        *,
        raise_exception: bool = False,
    ) -> Optional[Dict]:
        """
        Fetch a single evaluation testcase by unique_id.
        """
        return self._get(
            f"/eval-framework/deepeval/uid/{unique_id}",
            params={},
            raise_exception=raise_exception,
        )

    def get_evaluation_testcase(
        self,
        *,
        id: Optional[int] = None,
        unique_id: Optional[str] = None,
        raise_exception: bool = False,
    ) -> Optional[Dict]:
        if id is not None:
            return self.get_evaluation_testcase_by_id(
                id, raise_exception=raise_exception
            )
        if unique_id is not None:
            return self.get_evaluation_testcase_by_unique_id(
                unique_id, raise_exception=raise_exception
            )
        raise ValueError("Either id or unique_id must be provided")

    def compare_testcases(
        self,
        *,
        testcase_a_id: int,
        testcase_b_id: int,
        raise_exception: bool = False,
    ) -> Optional[dict]:
        """
        Compare two evaluation testcases.
        """
        return self._get(
            "/eval-framework/deepeval/evaluation-testcases/compare",
            params={
                "testcase_a_id": testcase_a_id,
                "testcase_b_id": testcase_b_id,
            },
            raise_exception=raise_exception,
        )

    def compare_latest_by_labels(
        self,
        *,
        label_a: str,
        label_b: str,
        raise_exception: bool = False,
    ) -> Optional[dict]:
        """
        Compare the latest evaluation testcases for two labels.
        """
        return self._get(
            "/eval-framework/deepeval/evaluation-testcases/compare-latest",
            params={
                "label_a": label_a,
                "label_b": label_b,
            },
            raise_exception=raise_exception,
        )

    def compare_last_two_by_label(
        self,
        *,
        label: str,
        raise_exception: bool = False,
    ) -> Optional[dict]:
        """
        Compare the last two evaluation testcases for a given label.
        """
        return self._get(
            "/eval-framework/deepeval/evaluation-testcases/compare-last-two",
            params={
                "label": label,
            },
            raise_exception=raise_exception,
        )

    @overload
    def text_eval(
        self,
        config: EvalConfig,
        *,
        raise_exception: bool = False,
    ) -> Optional[dict]: ...

    @overload
    def text_eval(
        self,
        *,
        data: List[TextInputItem],
        metrics: List[MetricConfig],
        component: str = "unknown",
        label: str | None = None,
        raise_exception: bool = False,
    ) -> Optional[dict]: ...

    def text_eval(
        self,
        config: EvalConfig | None = None,
        *,
        data: List[TextInputItem] | None = None,
        metrics: List[MetricConfig] | None = None,
        component: str = "unknown",
        label: str | None = None,
        raise_exception: bool = False,
    ) -> Optional[dict]:
        if config is None:
            config = EvalConfig(
                data=data,
                metrics=metrics,
                component=component,
                label=label,
            )

        return self._request(
            "/deepeval/text-eval", config.model_dump(), raise_exception
        )

    def text_eval_background(
        self,
        data: List[TextInputItem],
        metrics: List[MetricConfig],
        raise_exception: bool = False,
        component: str = "unknown",
        label: Union[str, None] = None,
    ) -> Optional[dict]:
        """Run background text evaluation (async job)."""
        payload = EvalConfig.model_construct(
            data=data, metrics=metrics, component=component, version=label
        ).model_dump()
        return self._request("/deepeval/text-eval/background", payload, raise_exception)

    @overload
    def schema_eval(
        self,
        *,
        data: List[SchemaInputItem],
        metrics: List[SchemaMetricConfig],
        component: str = "unknown",
        label: str | None = None,
        raise_exception: bool = False,
    ) -> Optional[dict]: ...

    @overload
    def schema_eval(
        self,
        config: SchemaEvalConfig,
        *,
        raise_exception: bool = False,
    ) -> Optional[dict]: ...

    def schema_eval(
        self,
        config: SchemaEvalConfig | None = None,
        *,
        data: List[SchemaInputItem] | None = None,
        metrics: List[SchemaMetricConfig] | None = None,
        component: str = "unknown",
        label: str | None = None,
        raise_exception: bool = False,
    ) -> Optional[dict]:
        if config is None:
            if data is None or metrics is None:
                raise ValueError(
                    "Either `config` or both `data` and `metrics` must be provided"
                )

            config = SchemaEvalConfig(
                data=data,
                metrics=metrics,
                component=component,
                label=label,
            )

        return self._request(
            "/deepeval/schema-eval",
            config.model_dump(),
            raise_exception,
        )

    def schema_eval_background(
        self,
        data: List[SchemaInputItem],
        metrics: List[SchemaMetricConfig],
        raise_exception: bool = False,
        component: str = "unknown",
        label: Union[str, None] = None,
    ) -> Optional[dict]:
        """Run background schema evaluation (async job)."""
        payload = SchemaEvalConfig.model_construct(
            data=data, metrics=metrics, component=component, version=label
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
        label: Union[str, None] = None,
    ) -> Optional[dict]:
        """Randomly run text_eval based on a probability between 0 and 1."""
        self._validate_chance(chance)
        return (
            self.text_eval(
                data=data,
                metrics=metrics,
                raise_exception=raise_exception,
                component=component,
                label=label,
            )
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
        label: Union[str, None] = None,
    ) -> Optional[dict]:
        """Randomly run text_eval_background based on a probability between 0 and 1."""
        self._validate_chance(chance)
        return (
            self.text_eval_background(
                data, metrics, raise_exception, component=component, label=label
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
        label: Union[str, None] = None,
    ) -> Optional[dict]:
        """Randomly run schema_eval based on a probability between 0 and 1."""
        self._validate_chance(chance)
        return (
            self.schema_eval(
                data=data,
                metrics=metrics,
                raise_exception=raise_exception,
                component=component,
                label=label,
            )
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
        label: Union[str, None] = None,
    ) -> Optional[dict]:
        """Randomly run text_eval_background based on a probability between 0 and 1."""
        self._validate_chance(chance)
        return (
            self.schema_eval_background(
                data, metrics, raise_exception, component=component, label=label
            )
            if random.random() <= chance
            else None
        )

    @staticmethod
    def _validate_chance(chance: float) -> None:
        """Ensure chance is a valid probability between 0 and 1."""
        if not (0 <= chance <= 1):
            raise ValueError("chance must be between 0 and 1.")
