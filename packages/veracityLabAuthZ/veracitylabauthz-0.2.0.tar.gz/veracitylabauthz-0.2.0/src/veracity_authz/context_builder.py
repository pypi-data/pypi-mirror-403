"""Helpers for building Cedar request payloads."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class CedarRequest:
  """Cedar request payload representation."""

  principal: Mapping[str, Any]
  action: Mapping[str, Any]
  resource: Mapping[str, Any]
  context: Mapping[str, Any] = field(default_factory=dict)

  def to_dict(self) -> dict[str, Any]:
    """Return a Cedar-compatible request payload."""
    return {
      "principal": dict(self.principal),
      "action": dict(self.action),
      "resource": dict(self.resource),
      "context": dict(self.context),
    }


def build_request(
  *,
  principal: Mapping[str, Any],
  action: Mapping[str, Any],
  resource: Mapping[str, Any],
  context: Mapping[str, Any] | None = None,
) -> CedarRequest:
  """Construct a CedarRequest from component mappings."""
  return CedarRequest(
    principal=principal,
    action=action,
    resource=resource,
    context=context or {},
  )
