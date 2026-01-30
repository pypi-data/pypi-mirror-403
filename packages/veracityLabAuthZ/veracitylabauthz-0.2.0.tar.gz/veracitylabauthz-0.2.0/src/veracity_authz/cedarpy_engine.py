"""Cedar evaluation engine powered by cedarpy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from veracity_authz.context_builder import CedarRequest
from veracity_authz.exceptions import CedarEvaluationError
from veracity_authz.types import CedarDecision

try:
  from cedarpy import is_authorized  # type: ignore
  from cedarpy import Decision  # type: ignore
except ImportError:  # pragma: no cover
  is_authorized = None
  Decision = None


@dataclass(frozen=True)
class CedarPyConfig:
  """Configuration for the cedarpy evaluator."""

  policies: str
  entities: list | str
  schema: str | None = None


class CedarPyEngine:
  """Evaluate Cedar policies using the cedarpy bindings."""

  def __init__(self, config: CedarPyConfig) -> None:
    self._config = config

  def __call__(self, request: CedarRequest) -> CedarDecision:
    if is_authorized is None:
      raise CedarEvaluationError("cedarpy is not installed. Install veracityLabAuthZ[cedarpy].")

    payload = request.to_dict()
    payload["principal"] = _render_entity(payload["principal"])
    payload["action"] = _render_entity(payload["action"])
    payload["resource"] = _render_entity(payload["resource"])

    try:
      result = is_authorized(
        payload,
        self._config.policies,
        self._config.entities,
        schema=self._config.schema,
      )
    except Exception as exc:  # pragma: no cover - defensive
      raise CedarEvaluationError("Failed to evaluate Cedar policies.") from exc

    allowed = getattr(result, "allowed", None)
    if allowed is None and Decision is not None:
      allowed = getattr(result, "decision", None) == Decision.Allow

    diagnostics = getattr(result, "diagnostics", None)
    errors = tuple(getattr(result, "errors", []) or ())

    return CedarDecision(
      allowed=bool(allowed),
      reason="cedarpy",
      diagnostics=diagnostics,
      errors=errors,
    )


def _render_entity(value: Mapping[str, Any] | str) -> str:
  """Render a Cedar entity UID from a mapping or pass through strings."""
  if isinstance(value, str):
    return value

  entity_type = value.get("type") or value.get("entity_type")
  entity_id = value.get("id") or value.get("entity_id")
  if not entity_type or not entity_id:
    raise CedarEvaluationError("Entity mapping must include 'type' and 'id'.")

  return f'{entity_type}::"{entity_id}"'
