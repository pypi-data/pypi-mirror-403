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

  def _build_client(self):
    policies = """
permit(principal, action, resource)
when {
  principal in Group::"Analysts"
  && action == Action::"workspace:read"
  && resource.classification == "public"
};

permit(principal, action, resource)
when {
  principal.department == "research"
  && action == Action::"workspace:read"
  && resource.region == "us"
};

permit(principal, action, resource)
when {
  principal == User::"alice"
  && action == Action::"workspace:write"
  && resource.classification == "public"
};

permit(principal, action, resource)
when { principal.role == "admin" };

permit(principal, action, resource)
when { context.request_ip == "10.0.0.1" && action == Action::"workspace:read" };

permit(principal, action, resource)
when {
  principal.department == "research"
  && action == Action::"workspace:write"
  && resource.classification == "public"
  && context.mfa == true
};

permit(principal, action, resource)
when {
  principal.role == "contractor"
  && action == Action::"workspace:read"
  && resource.classification == "public"
  && context.contract_active == true
};

forbid(principal, action, resource)
when { action == Action::"workspace:delete" };

forbid(principal, action, resource)
when { context.suspended == true };

forbid(principal, action, resource)
when {
  resource.classification == "secret"
  && !(principal in Group::"Security")
};
""".strip()

    entities = [
      {
        "uid": {"type": "User", "id": "alice"},
        "attrs": {"role": "analyst", "department": "research"},
        "parents": [{"type": "Group", "id": "Analysts"}],
      },
      {
        "uid": {"type": "User", "id": "bob"},
        "attrs": {"role": "contractor", "department": "sales"},
        "parents": [],
      },
      {
        "uid": {"type": "User", "id": "carla"},
        "attrs": {"role": "admin", "department": "ops"},
        "parents": [],
      },
      {
        "uid": {"type": "User", "id": "erin"},
        "attrs": {"role": "employee", "department": "research"},
        "parents": [],
      },
      {
        "uid": {"type": "User", "id": "dave"},
        "attrs": {"role": "analyst", "department": "research"},
        "parents": [{"type": "Group", "id": "Security"}],
      },
      {
        "uid": {"type": "Group", "id": "Analysts"},
        "attrs": {},
        "parents": [],
      },
      {
        "uid": {"type": "Group", "id": "Security"},
        "attrs": {},
        "parents": [],
      },
      {
        "uid": {"type": "Workspace", "id": "ws-public"},
        "attrs": {
          "classification": "public",
          "region": "us",
        },
        "parents": [],
      },
      {
        "uid": {"type": "Workspace", "id": "ws-secret"},
        "attrs": {
          "classification": "secret",
          "region": "us",
        },
        "parents": [],
      },
      {
        "uid": {"type": "Workspace", "id": "ws-eu"},
        "attrs": {
          "classification": "public",
          "region": "eu",
        },
        "parents": [],
      },
      {
        "uid": {"type": "Action", "id": "workspace:read"},
        "attrs": {},
        "parents": [],
      },
      {
        "uid": {"type": "Action", "id": "workspace:write"},
        "attrs": {},
        "parents": [],
      },
      {
        "uid": {"type": "Action", "id": "workspace:delete"},
        "attrs": {},
        "parents": [],
      },
    ]

    engine = CedarPyEngine(CedarPyConfig(policies=policies, entities=entities))
    return CedarClient(engine)

  @staticmethod
  def _build_request(principal_id, action_id, resource_id, context):
    return build_request(
      principal={"type": "User", "id": principal_id},
      action={"type": "Action", "id": action_id},
      resource={"type": "Workspace", "id": resource_id},
      context=context,
    )

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

  def test_cedarpy_policy_matrix_for_single_user(self):
    client = self._build_client()
    base_context = {
      "request_ip": "10.0.0.2",
      "suspended": False,
      "mfa": False,
      "contract_active": False,
    }
    cases = [
      (
        "alice read public allowed by multiple permits",
        "alice",
        "workspace:read",
        "ws-public",
        base_context,
        True,
      ),
      (
        "alice read secret denied despite matching permits",
        "alice",
        "workspace:read",
        "ws-secret",
        base_context,
        False,
      ),
      (
        "alice write public allowed by principal rule",
        "alice",
        "workspace:write",
        "ws-public",
        base_context,
        True,
      ),
      (
        "alice delete denied by explicit forbid",
        "alice",
        "workspace:delete",
        "ws-public",
        base_context,
        False,
      ),
      (
        "alice suspension denies even allowed actions",
        "alice",
        "workspace:read",
        "ws-public",
        {**base_context, "suspended": True},
        False,
      ),
      (
        "bob read public allowed only with active contract",
        "bob",
        "workspace:read",
        "ws-public",
        {**base_context, "contract_active": True, "request_ip": "10.0.0.2"},
        True,
      ),
      (
        "bob read public denied when contract inactive",
        "bob",
        "workspace:read",
        "ws-public",
        {**base_context, "contract_active": False, "request_ip": "10.0.0.2"},
        False,
      ),
      (
        "carla admin read public allowed",
        "carla",
        "workspace:read",
        "ws-public",
        {**base_context, "request_ip": "10.0.0.2"},
        True,
      ),
      (
        "carla admin write secret denied by forbid",
        "carla",
        "workspace:write",
        "ws-secret",
        {**base_context, "request_ip": "10.0.0.2"},
        False,
      ),
      (
        "dave security group can read secret",
        "dave",
        "workspace:read",
        "ws-secret",
        {**base_context, "request_ip": "10.0.0.2"},
        True,
      ),
      (
        "erin research write denied without mfa",
        "erin",
        "workspace:write",
        "ws-public",
        {**base_context, "mfa": False, "request_ip": "10.0.0.2"},
        False,
      ),
      (
        "erin research write allowed with mfa",
        "erin",
        "workspace:write",
        "ws-public",
        {**base_context, "mfa": True, "request_ip": "10.0.0.2"},
        True,
      ),
      (
        "erin research read us allowed",
        "erin",
        "workspace:read",
        "ws-public",
        {**base_context, "request_ip": "10.0.0.2"},
        True,
      ),
      (
        "erin research read eu denied",
        "erin",
        "workspace:read",
        "ws-eu",
        {**base_context, "request_ip": "10.0.0.2"},
        False,
      ),
      (
        "bob read public allowed by ip rule",
        "bob",
        "workspace:read",
        "ws-public",
        {**base_context, "request_ip": "10.0.0.1"},
        True,
      ),
    ]

    for label, principal_id, action_id, resource_id, context, expected in cases:
      with self.subTest(case=label):
        request = self._build_request(principal_id, action_id, resource_id, context)
        decision = client.evaluate(request)
        self.assertEqual(decision.allowed, expected)


if __name__ == "__main__":
  unittest.main()
