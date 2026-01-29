"""Integration tests for cedarpy-based evaluator."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
sys.path.append(str(SRC_ROOT))

from veracity_authz import CedarClient, CedarPyConfig, CedarPyEngine
from veracity_authz.context_builder import build_request
from veracity_authz.cedarpy_engine import is_authorized


class CedarPyEngineTests(unittest.TestCase):
  def setUp(self):
    if is_authorized is None:
      raise unittest.SkipTest("cedarpy is not installed")

  def test_cedarpy_allows_simple_policy(self):
    policies = "permit(principal, action, resource);"
    engine = CedarPyEngine(CedarPyConfig(policies=policies, entities=[]))
    client = CedarClient(engine)

    request = build_request(
      principal={"type": "User", "id": "user-1"},
      action={"type": "Action", "id": "workspace:read"},
      resource={"type": "Workspace", "id": "ws-1"},
    )

    decision = client.evaluate(request)
    self.assertTrue(decision.allowed)


if __name__ == "__main__":
  unittest.main()
