"""Cedar evaluation client abstraction."""

from __future__ import annotations

from typing import Callable, Optional, Protocol

from veracity_authz.context_builder import CedarRequest
from veracity_authz.exceptions import CedarEvaluationError
from veracity_authz.types import CedarDecision


class CedarEvaluator(Protocol):
  """Protocol for Cedar evaluation backends."""

  def __call__(self, request: CedarRequest) -> CedarDecision:
    ...


class CedarClient:
  """Evaluate Cedar policies using a provided backend."""

  def __init__(self, evaluator: Optional[CedarEvaluator] = None) -> None:
    self._evaluator = evaluator

  def evaluate(self, request: CedarRequest) -> CedarDecision:
    """Evaluate the provided Cedar request."""
    if self._evaluator is None:
      raise CedarEvaluationError("No Cedar evaluator configured.")
    return self._evaluator(request)


def allow_all_evaluator(_: CedarRequest) -> CedarDecision:
  """Evaluator that allows all requests (use only in development)."""
  return CedarDecision.allow("allow_all_evaluator")
