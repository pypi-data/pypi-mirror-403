"""
QAuth Python SDK Tests

These tests verify the QAuth SDK functionality.
Note: Full integration tests require the Rust library to be built with maturin.
"""

import pytest
import json
import base64
import time
import os
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from enum import Enum


# Mock implementations for testing until the Rust library is built
class Effect(Enum):
    """Authorization effect."""

    ALLOW = "allow"
    DENY = "deny"


@dataclass
class TokenPayload:
    """Token payload structure."""

    sub: bytes
    iss: str
    aud: List[str]
    exp: int
    iat: int
    nbf: int
    jti: bytes
    rid: bytes
    pol: str
    ctx: bytes
    cst: Dict[str, Any]


@dataclass
class EvaluationResult:
    """Policy evaluation result."""

    effect: Effect
    matched_rule: Optional[str]
    reason: str


class MockQAuthServer:
    """Mock server for testing."""

    def __init__(self, issuer: str, audience: str):
        self.issuer = issuer
        self.audience = audience
        self._signing_keys = os.urandom(32)
        self._encryption_key = os.urandom(32)

    def create_token(
        self,
        subject: str,
        policy_ref: str,
        audience: Optional[str] = None,
        validity_seconds: int = 3600,
        client_key: Optional[bytes] = None,
        device_key: Optional[bytes] = None,
        claims: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create a mock token for testing."""
        now = int(time.time())
        payload = {
            "sub": subject,
            "iss": self.issuer,
            "aud": [audience or self.audience],
            "exp": now + validity_seconds,
            "iat": now,
            "nbf": now,
            "jti": os.urandom(16).hex(),
            "rid": os.urandom(16).hex(),
            "pol": policy_ref,
            "ctx": os.urandom(32).hex(),
            "cst": claims or {},
        }
        return base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()

    def validate_token(self, token: str) -> TokenPayload:
        """Validate and decode a token."""
        payload_json = base64.urlsafe_b64decode(token.encode())
        payload = json.loads(payload_json)
        return TokenPayload(
            sub=payload["sub"].encode() if isinstance(payload["sub"], str) else payload["sub"],
            iss=payload["iss"],
            aud=payload["aud"],
            exp=payload["exp"],
            iat=payload["iat"],
            nbf=payload["nbf"],
            jti=bytes.fromhex(payload["jti"]) if isinstance(payload["jti"], str) else payload["jti"],
            rid=bytes.fromhex(payload["rid"]) if isinstance(payload["rid"], str) else payload["rid"],
            pol=payload["pol"],
            ctx=bytes.fromhex(payload["ctx"]) if isinstance(payload["ctx"], str) else payload["ctx"],
            cst=payload["cst"],
        )

    def get_public_keys(self) -> Dict[str, bytes]:
        """Get public keys for sharing with validators."""
        return {
            "ed25519": os.urandom(32),
            "mldsa": os.urandom(1952),
        }


class MockQAuthClient:
    """Mock client for testing."""

    def __init__(self):
        self._private_key = os.urandom(32)
        self._public_key = os.urandom(32)

    @property
    def public_key(self) -> bytes:
        """Get client public key."""
        return self._public_key

    def create_proof(
        self,
        method: str,
        uri: str,
        token: str,
        body: Optional[bytes] = None,
    ) -> str:
        """Create proof of possession."""
        proof_data = {
            "timestamp": int(time.time() * 1000),
            "method": method,
            "uri": uri,
            "token_hash": token[:16],
            "body_hash": body.hex()[:16] if body else None,
            "signature": os.urandom(64).hex(),
        }
        return base64.urlsafe_b64encode(json.dumps(proof_data).encode()).decode()


class MockPolicyEngine:
    """Mock policy engine for testing."""

    def __init__(self):
        self._policies: Dict[str, Any] = {}

    def load_policy(self, policy: Dict[str, Any]) -> None:
        """Load a policy."""
        self._policies[policy["id"]] = policy

    def evaluate(self, policy_id: str, context: Dict[str, Any]) -> EvaluationResult:
        """Evaluate authorization."""
        policy = self._policies.get(policy_id)
        if not policy:
            return EvaluationResult(
                effect=Effect.DENY, matched_rule=None, reason="Policy not found"
            )

        resource_path = context.get("resource", {}).get("path", "")
        action = context.get("request", {}).get("action", "")

        for rule in policy.get("rules", []):
            if self._match_resource(resource_path, rule.get("resources", [])):
                if self._match_action(action, rule.get("actions", [])):
                    return EvaluationResult(
                        effect=Effect.ALLOW if rule["effect"] == "allow" else Effect.DENY,
                        matched_rule=rule.get("id"),
                        reason=f"Matched rule: {rule.get('id')}",
                    )

        return EvaluationResult(
            effect=Effect.DENY, matched_rule=None, reason="No matching rule"
        )

    def _match_resource(self, path: str, patterns: List[str]) -> bool:
        """Match resource path against patterns."""
        import re

        for pattern in patterns:
            # Use placeholder to avoid replacing ** incorrectly
            regex = pattern.replace("**", "\x00DOUBLE\x00")
            regex = regex.replace("*", "[^/]*")
            regex = regex.replace("\x00DOUBLE\x00", ".*")
            if re.match(f"^{regex}$", path):
                return True
        return False

    def _match_action(self, action: str, actions: List[str]) -> bool:
        """Match action against allowed actions."""
        return action in actions or "*" in actions


class TestQAuthServer:
    """Tests for QAuthServer."""

    def test_create_server(self):
        """Should create a server instance."""
        server = MockQAuthServer(
            issuer="https://auth.example.com", audience="https://api.example.com"
        )
        assert server is not None
        assert server.issuer == "https://auth.example.com"
        assert server.audience == "https://api.example.com"

    def test_create_token(self):
        """Should create a token."""
        server = MockQAuthServer(
            issuer="https://auth.example.com", audience="https://api.example.com"
        )

        token = server.create_token(
            subject="user-123",
            policy_ref="urn:qauth:policy:default",
            validity_seconds=3600,
            claims={"email": "user@example.com", "roles": ["user", "premium"]},
        )

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_validate_token(self):
        """Should validate a token."""
        server = MockQAuthServer(
            issuer="https://auth.example.com", audience="https://api.example.com"
        )

        token = server.create_token(
            subject="user-123", policy_ref="urn:qauth:policy:default"
        )

        payload = server.validate_token(token)

        assert payload.sub == b"user-123"
        assert payload.iss == "https://auth.example.com"
        assert "https://api.example.com" in payload.aud
        assert payload.pol == "urn:qauth:policy:default"

    def test_token_includes_custom_claims(self):
        """Should include custom claims in token."""
        server = MockQAuthServer(
            issuer="https://auth.example.com", audience="https://api.example.com"
        )

        token = server.create_token(
            subject="user-123",
            policy_ref="urn:qauth:policy:default",
            claims={"department": "engineering", "level": 5},
        )

        payload = server.validate_token(token)

        assert payload.cst["department"] == "engineering"
        assert payload.cst["level"] == 5

    def test_token_expiration(self):
        """Should set correct expiration time."""
        server = MockQAuthServer(
            issuer="https://auth.example.com", audience="https://api.example.com"
        )

        validity = 7200  # 2 hours
        token = server.create_token(
            subject="user-123",
            policy_ref="urn:qauth:policy:default",
            validity_seconds=validity,
        )

        payload = server.validate_token(token)

        expected_exp = payload.iat + validity
        assert payload.exp == expected_exp

    def test_get_public_keys(self):
        """Should return public keys."""
        server = MockQAuthServer(
            issuer="https://auth.example.com", audience="https://api.example.com"
        )

        keys = server.get_public_keys()

        assert "ed25519" in keys
        assert "mldsa" in keys
        assert len(keys["ed25519"]) == 32
        assert len(keys["mldsa"]) == 1952


class TestQAuthClient:
    """Tests for QAuthClient."""

    def test_create_client(self):
        """Should create a client instance."""
        client = MockQAuthClient()
        assert client is not None

    def test_generate_public_key(self):
        """Should generate a public key."""
        client = MockQAuthClient()
        public_key = client.public_key

        assert isinstance(public_key, bytes)
        assert len(public_key) == 32

    def test_unique_keys_per_client(self):
        """Should generate unique keys for each client."""
        client1 = MockQAuthClient()
        client2 = MockQAuthClient()

        assert client1.public_key != client2.public_key

    def test_create_proof(self):
        """Should create proof of possession."""
        client = MockQAuthClient()
        proof = client.create_proof("GET", "/api/resource", "test-token")

        assert proof is not None
        assert isinstance(proof, str)
        assert len(proof) > 0

    def test_create_proof_with_body(self):
        """Should create proof with request body."""
        client = MockQAuthClient()
        body = b"request body content"
        proof = client.create_proof("POST", "/api/resource", "test-token", body)

        assert proof is not None
        assert isinstance(proof, str)


class TestPolicyEngine:
    """Tests for PolicyEngine."""

    def test_create_policy_engine(self):
        """Should create a policy engine."""
        engine = MockPolicyEngine()
        assert engine is not None

    def test_load_policy(self):
        """Should load a policy."""
        engine = MockPolicyEngine()

        engine.load_policy(
            {
                "id": "urn:qauth:policy:test",
                "version": "2026-01-30",
                "issuer": "https://auth.example.com",
                "rules": [
                    {
                        "id": "read-projects",
                        "effect": "allow",
                        "resources": ["projects/*"],
                        "actions": ["read", "list"],
                    }
                ],
            }
        )

        # Policy loaded successfully if no exception
        assert True

    def test_allow_matching_request(self):
        """Should allow matching requests."""
        engine = MockPolicyEngine()

        engine.load_policy(
            {
                "id": "urn:qauth:policy:test",
                "version": "2026-01-30",
                "issuer": "https://auth.example.com",
                "rules": [
                    {
                        "id": "read-projects",
                        "effect": "allow",
                        "resources": ["projects/*"],
                        "actions": ["read", "list"],
                    }
                ],
            }
        )

        result = engine.evaluate(
            "urn:qauth:policy:test",
            {
                "subject": {"id": "user-123"},
                "resource": {"path": "projects/456"},
                "request": {"action": "read"},
            },
        )

        assert result.effect == Effect.ALLOW
        assert result.matched_rule == "read-projects"

    def test_deny_non_matching_request(self):
        """Should deny non-matching requests."""
        engine = MockPolicyEngine()

        engine.load_policy(
            {
                "id": "urn:qauth:policy:test",
                "version": "2026-01-30",
                "issuer": "https://auth.example.com",
                "rules": [
                    {
                        "id": "read-projects",
                        "effect": "allow",
                        "resources": ["projects/*"],
                        "actions": ["read"],
                    }
                ],
            }
        )

        result = engine.evaluate(
            "urn:qauth:policy:test",
            {
                "subject": {"id": "user-123"},
                "resource": {"path": "projects/456"},
                "request": {"action": "delete"},
            },
        )

        assert result.effect == Effect.DENY

    def test_deny_unknown_policy(self):
        """Should deny for unknown policy."""
        engine = MockPolicyEngine()

        result = engine.evaluate(
            "urn:qauth:policy:unknown",
            {
                "subject": {"id": "user-123"},
                "resource": {"path": "projects/456"},
                "request": {"action": "read"},
            },
        )

        assert result.effect == Effect.DENY
        assert "not found" in result.reason

    def test_wildcard_actions(self):
        """Should match wildcard actions."""
        engine = MockPolicyEngine()

        engine.load_policy(
            {
                "id": "urn:qauth:policy:admin",
                "version": "2026-01-30",
                "issuer": "https://auth.example.com",
                "rules": [
                    {
                        "id": "admin-all",
                        "effect": "allow",
                        "resources": ["admin/**"],
                        "actions": ["*"],
                    }
                ],
            }
        )

        result = engine.evaluate(
            "urn:qauth:policy:admin",
            {
                "subject": {"id": "admin-1"},
                "resource": {"path": "admin/users/123"},
                "request": {"action": "delete"},
            },
        )

        assert result.effect == Effect.ALLOW

    def test_double_wildcard_resources(self):
        """Should match double wildcard resources."""
        engine = MockPolicyEngine()

        engine.load_policy(
            {
                "id": "urn:qauth:policy:nested",
                "version": "2026-01-30",
                "issuer": "https://auth.example.com",
                "rules": [
                    {
                        "id": "nested-read",
                        "effect": "allow",
                        "resources": ["data/**"],
                        "actions": ["read"],
                    }
                ],
            }
        )

        result = engine.evaluate(
            "urn:qauth:policy:nested",
            {
                "subject": {"id": "user-1"},
                "resource": {"path": "data/level1/level2/level3/file.txt"},
                "request": {"action": "read"},
            },
        )

        assert result.effect == Effect.ALLOW


class TestIntegration:
    """Integration tests."""

    def test_complete_auth_flow(self):
        """Should complete full authentication flow."""
        # 1. Create server
        server = MockQAuthServer(
            issuer="https://auth.example.com", audience="https://api.example.com"
        )

        # 2. Create client
        client = MockQAuthClient()
        public_key = client.public_key
        assert len(public_key) == 32

        # 3. Create token
        token = server.create_token(
            subject="user-123",
            policy_ref="urn:qauth:policy:default",
            validity_seconds=3600,
            client_key=public_key,
            claims={"email": "user@example.com", "roles": ["user"]},
        )

        # 4. Create proof
        proof = client.create_proof("GET", "/api/users/me", token)

        # 5. Validate token
        payload = server.validate_token(token)
        assert payload.sub == b"user-123"

        # 6. Verify proof exists
        assert proof is not None

    def test_complete_authorization_flow(self):
        """Should complete authorization flow."""
        server = MockQAuthServer(
            issuer="https://auth.example.com", audience="https://api.example.com"
        )

        engine = MockPolicyEngine()

        # Load policy
        engine.load_policy(
            {
                "id": "urn:qauth:policy:api-access",
                "version": "2026-01-30",
                "issuer": "https://auth.example.com",
                "rules": [
                    {
                        "id": "read-projects",
                        "effect": "allow",
                        "resources": ["projects/*"],
                        "actions": ["read", "list"],
                    },
                    {
                        "id": "write-projects",
                        "effect": "allow",
                        "resources": ["projects/*/files"],
                        "actions": ["write", "create"],
                    },
                ],
            }
        )

        # Create token
        token = server.create_token(
            subject="user-123",
            policy_ref="urn:qauth:policy:api-access",
            claims={"department": "engineering"},
        )

        # Validate token
        payload = server.validate_token(token)

        # Evaluate authorization
        result = engine.evaluate(
            "urn:qauth:policy:api-access",
            {
                "subject": {
                    "id": payload.sub.decode(),
                    "attributes": payload.cst,
                },
                "resource": {"path": "projects/456"},
                "request": {"action": "read"},
            },
        )

        assert result.effect == Effect.ALLOW


class TestEdgeCases:
    """Edge case tests."""

    def test_empty_claims(self):
        """Should handle empty claims."""
        server = MockQAuthServer(
            issuer="https://auth.example.com", audience="https://api.example.com"
        )

        token = server.create_token(
            subject="user-123", policy_ref="urn:qauth:policy:default"
        )

        payload = server.validate_token(token)
        assert payload.cst == {}

    def test_special_characters_in_subject(self):
        """Should handle special characters in subject."""
        server = MockQAuthServer(
            issuer="https://auth.example.com", audience="https://api.example.com"
        )

        subject = "user+special@example.com"
        token = server.create_token(subject=subject, policy_ref="urn:qauth:policy:default")

        payload = server.validate_token(token)
        assert payload.sub == subject.encode()

    def test_complex_nested_claims(self):
        """Should handle complex nested claims."""
        server = MockQAuthServer(
            issuer="https://auth.example.com", audience="https://api.example.com"
        )

        claims = {
            "metadata": {
                "created": "2026-01-30",
                "tags": ["a", "b", "c"],
                "nested": {"deep": {"value": 42}},
            }
        }

        token = server.create_token(
            subject="user-123", policy_ref="urn:qauth:policy:default", claims=claims
        )

        payload = server.validate_token(token)
        assert payload.cst == claims

    def test_unicode_subject(self):
        """Should handle unicode in subject."""
        server = MockQAuthServer(
            issuer="https://auth.example.com", audience="https://api.example.com"
        )

        subject = "user-\u4e2d\u6587-123"  # Chinese characters
        token = server.create_token(subject=subject, policy_ref="urn:qauth:policy:default")

        payload = server.validate_token(token)
        assert payload.sub == subject.encode()

    def test_large_claims(self):
        """Should handle large claims."""
        server = MockQAuthServer(
            issuer="https://auth.example.com", audience="https://api.example.com"
        )

        claims = {
            "permissions": [f"permission-{i}" for i in range(100)],
            "groups": [f"group-{i}" for i in range(50)],
        }

        token = server.create_token(
            subject="user-123", policy_ref="urn:qauth:policy:default", claims=claims
        )

        payload = server.validate_token(token)
        assert len(payload.cst["permissions"]) == 100
        assert len(payload.cst["groups"]) == 50


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
