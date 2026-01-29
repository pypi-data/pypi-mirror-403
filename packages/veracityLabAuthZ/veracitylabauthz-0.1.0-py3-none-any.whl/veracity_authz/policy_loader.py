"""Utilities for loading Cedar policy bundles."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class PolicyBundle:
  """Loaded Cedar policy bundle."""

  policies: tuple[str, ...]


def load_policy_bundle(paths: Iterable[str | Path]) -> PolicyBundle:
  """Load Cedar policies from the provided file paths."""
  policies: list[str] = []
  for path in paths:
    file_path = Path(path)
    policies.append(file_path.read_text())
  return PolicyBundle(policies=tuple(policies))
