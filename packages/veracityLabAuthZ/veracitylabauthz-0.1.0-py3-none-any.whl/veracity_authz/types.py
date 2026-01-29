"""Shared types for Cedar authorization."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional


@dataclass(frozen=True)
class CedarDecision:
  """Result of a Cedar authorization evaluation."""

  allowed: bool
  reason: Optional[str] = None
  diagnostics: Optional[dict] = None
  errors: tuple[str, ...] = ()

  @classmethod
  def allow(cls, reason: str | None = None) -> "CedarDecision":
    return cls(allowed=True, reason=reason)

  @classmethod
  def deny(
    cls,
    reason: str | None = None,
    errors: Iterable[str] | None = None,
  ) -> "CedarDecision":
    return cls(
      allowed=False,
      reason=reason,
      errors=tuple(errors or ()),
    )
