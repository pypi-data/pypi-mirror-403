"""Basic tests for the veracityLabAuthZ package."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
sys.path.append(str(SRC_ROOT))

from veracity_authz.cedar_client import CedarClient, allow_all_evaluator
from veracity_authz.context_builder import build_request
from veracity_authz.exceptions import CedarEvaluationError
from veracity_authz.types import CedarDecision


class CedarAuthzTests(unittest.TestCase):
  def test_request_to_dict(self):
    request = build_request(
      principal={"type": "User", "id": "user-1"},
      action={"type": "Action", "id": "workspace:read"},
      resource={"type": "Workspace", "id": "ws-1"},
      context={"scopes": ["assets:read"]},
    )
    payload = request.to_dict()
    self.assertEqual(payload["principal"]["id"], "user-1")
    self.assertEqual(payload["action"]["id"], "workspace:read")
    self.assertEqual(payload["resource"]["id"], "ws-1")
    self.assertEqual(payload["context"]["scopes"], ["assets:read"])

  def test_client_requires_evaluator(self):
    client = CedarClient()
    request = build_request(
      principal={"type": "User", "id": "user-1"},
      action={"type": "Action", "id": "workspace:read"},
      resource={"type": "Workspace", "id": "ws-1"},
    )
    with self.assertRaises(CedarEvaluationError):
      client.evaluate(request)

  def test_allow_all_evaluator(self):
    client = CedarClient(allow_all_evaluator)
    request = build_request(
      principal={"type": "User", "id": "user-1"},
      action={"type": "Action", "id": "workspace:read"},
      resource={"type": "Workspace", "id": "ws-1"},
    )
    decision = client.evaluate(request)
    self.assertIsInstance(decision, CedarDecision)
    self.assertTrue(decision.allowed)


if __name__ == "__main__":
  unittest.main()
