"""LiteLLM callback for environmental impact metrics."""

from __future__ import annotations

import threading
from typing import Any

from ecologits.model_repository import ModelRepository
from ecologits.tracers.utils import llm_impacts
from litellm.integrations.custom_logger import CustomLogger
from prometheus_client import REGISTRY, Gauge, start_http_server

PROVIDER_PREFIXES = {
    "gpt-": "openai",
    "o1": "openai",
    "o3": "openai",
    "o4": "openai",
    "chatgpt": "openai",
    "claude": "anthropic",
    "gemini": "google_genai",
    "mistral": "mistralai",
    "codestral": "mistralai",
    "pixtral": "mistralai",
    "command": "cohere",
}

PROVIDER_MAP = {
    "openai": "openai",
    "anthropic": "anthropic",
    "google": "google_genai",
    "vertex_ai": "google_genai",
    "gemini": "google_genai",
    "mistral": "mistralai",
    "cohere": "cohere",
    "huggingface": "huggingface_hub",
}

_model_repo = ModelRepository.from_json()
_server_lock = threading.Lock()
_server_started = False


def _start_metrics_server(port: int) -> bool:
    global _server_started
    with _server_lock:
        if _server_started:
            return True
        try:
            start_http_server(port)
            _server_started = True
            return True
        except OSError:
            return False


def _get_or_create_gauge(name: str, description: str, labels: list[str]) -> Gauge:
    try:
        return Gauge(name, description, labels)
    except ValueError:
        return REGISTRY._names_to_collectors[name]


def _match_model(model_name: str) -> tuple[str, str] | None:
    if "/" in model_name:
        provider, name = model_name.split("/", 1)
        mapped_provider = PROVIDER_MAP.get(provider)
        if mapped_provider and _model_repo.find_model(mapped_provider, name):
            return mapped_provider, name

    for prefix, provider in PROVIDER_PREFIXES.items():
        if model_name.startswith(prefix):
            if _model_repo.find_model(provider, model_name):
                return provider, model_name
            break

    return None


class ImpactsCallback(CustomLogger):
    """LiteLLM callback that records environmental impact metrics to Prometheus.

    Args:
        prefix: Metric name prefix. Defaults to "litellm".
        labels: List of label names to attach to metrics.
            Defaults to ["model", "key_alias"].
        start_server: Whether to start a Prometheus HTTP server.
            Defaults to True.
        server_port: Port for the Prometheus HTTP server. Defaults to 8000.
    """

    def __init__(
        self,
        prefix: str = "litellm",
        labels: list[str] | None = None,
        start_server: bool = True,
        server_port: int = 8000,
    ):
        self.prefix = prefix
        self.labels = labels or ["model", "key_alias"]

        if start_server:
            _start_metrics_server(server_port)

        self._energy_kwh_min = _get_or_create_gauge(
            f"{prefix}_energy_kwh_min",
            "Minimum energy consumption in kWh",
            self.labels,
        )
        self._energy_kwh_max = _get_or_create_gauge(
            f"{prefix}_energy_kwh_max",
            "Maximum energy consumption in kWh",
            self.labels,
        )
        self._gwp_kgco2eq_min = _get_or_create_gauge(
            f"{prefix}_gwp_kgco2eq_min",
            "Minimum global warming potential in kgCO2eq",
            self.labels,
        )
        self._gwp_kgco2eq_max = _get_or_create_gauge(
            f"{prefix}_gwp_kgco2eq_max",
            "Maximum global warming potential in kgCO2eq",
            self.labels,
        )
        self._adpe_kgsbeq_min = _get_or_create_gauge(
            f"{prefix}_adpe_kgsbeq_min",
            "Minimum abiotic depletion potential in kgSbeq",
            self.labels,
        )
        self._adpe_kgsbeq_max = _get_or_create_gauge(
            f"{prefix}_adpe_kgsbeq_max",
            "Maximum abiotic depletion potential in kgSbeq",
            self.labels,
        )
        self._pe_mj_min = _get_or_create_gauge(
            f"{prefix}_pe_mj_min",
            "Minimum primary energy in MJ",
            self.labels,
        )
        self._pe_mj_max = _get_or_create_gauge(
            f"{prefix}_pe_mj_max",
            "Maximum primary energy in MJ",
            self.labels,
        )

    def _extract_labels(self, kwargs: dict[str, Any]) -> dict[str, str]:
        model = kwargs.get("model", "unknown")
        key_alias = (
            kwargs.get("litellm_params", {})
            .get("metadata", {})
            .get("user_api_key_alias", "unknown")
        )
        return {"model": model, "key_alias": key_alias}

    def _record_impacts(
        self,
        kwargs: dict[str, Any],
        response_obj: Any,
        start_time: Any,
        end_time: Any,
    ) -> None:
        model = kwargs.get("model", "unknown")
        matched = _match_model(model)
        if matched is None:
            return

        provider, model_name = matched

        usage = getattr(response_obj, "usage", None)
        if usage is None:
            return

        output_tokens = getattr(usage, "completion_tokens", 0) or 0
        if output_tokens == 0:
            return

        request_latency = (end_time - start_time).total_seconds()

        try:
            impacts = llm_impacts(
                provider=provider,
                model_name=model_name,
                output_token_count=output_tokens,
                request_latency=request_latency,
            )
        except Exception:
            return

        labels = self._extract_labels(kwargs)

        if impacts.energy is not None:
            self._energy_kwh_min.labels(**labels).set(impacts.energy.value.min)
            self._energy_kwh_max.labels(**labels).set(impacts.energy.value.max)

        if impacts.gwp is not None:
            self._gwp_kgco2eq_min.labels(**labels).set(impacts.gwp.value.min)
            self._gwp_kgco2eq_max.labels(**labels).set(impacts.gwp.value.max)

        if impacts.adpe is not None:
            self._adpe_kgsbeq_min.labels(**labels).set(impacts.adpe.value.min)
            self._adpe_kgsbeq_max.labels(**labels).set(impacts.adpe.value.max)

        if impacts.pe is not None:
            self._pe_mj_min.labels(**labels).set(impacts.pe.value.min)
            self._pe_mj_max.labels(**labels).set(impacts.pe.value.max)

    async def async_log_success_event(
        self,
        kwargs: dict[str, Any],
        response_obj: Any,
        start_time: Any,
        end_time: Any,
    ) -> None:
        self._record_impacts(kwargs, response_obj, start_time, end_time)

    async def async_log_failure_event(
        self,
        kwargs: dict[str, Any],
        response_obj: Any,
        start_time: Any,
        end_time: Any,
    ) -> None:
        pass


def create_callback(
    prefix: str = "litellm",
    labels: list[str] | None = None,
    start_server: bool = True,
    server_port: int = 8000,
) -> ImpactsCallback:
    """Create an ImpactsCallback instance.

    This is a convenience function for creating a callback with custom settings.
    For the default configuration, you can instantiate ImpactsCallback directly.

    Args:
        prefix: Metric name prefix. Defaults to "litellm".
        labels: List of label names. Defaults to ["model", "key_alias"].
        start_server: Whether to start a Prometheus HTTP server. Defaults to True.
        server_port: Port for the Prometheus HTTP server. Defaults to 8000.

    Returns:
        Configured ImpactsCallback instance.
    """
    return ImpactsCallback(
        prefix=prefix,
        labels=labels,
        start_server=start_server,
        server_port=server_port,
    )
