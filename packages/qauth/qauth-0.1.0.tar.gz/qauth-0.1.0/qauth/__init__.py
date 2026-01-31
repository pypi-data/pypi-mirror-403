"""
QAuth - QuantumAuth SDK for Python

Next-generation authentication and authorization protocol with post-quantum security.

Example usage:

    from qauth import QAuthServer, QAuthClient, PolicyEngine

    # Server-side: Generate issuer keys and create tokens
    server = QAuthServer(
        issuer="https://auth.example.com",
        audience="https://api.example.com"
    )

    token = server.create_token(
        subject="user-123",
        policy_ref="urn:qauth:policy:default",
        validity_seconds=3600,
    )

    # Client-side: Create proof of possession for API requests
    client = QAuthClient()
    proof = client.create_proof("GET", "/api/resource", token)

    # Server-side: Validate token and proof
    payload = server.validate_token(token)
    is_valid = server.validate_proof(proof, "GET", "/api/resource", token)

    # Policy-based authorization
    engine = PolicyEngine()
    engine.load_policy(policy_dict)
    result = engine.evaluate("urn:qauth:policy:default", context)
"""

from __future__ import annotations

import json
import secrets
import hashlib
import hmac
import time
from dataclasses import dataclass, field
from typing import Any, Optional, Union
from enum import Enum

__version__ = "0.1.0"
__protocol_version__ = "1.0.0"


class Effect(Enum):
    """Policy evaluation effect."""
    ALLOW = "allow"
    DENY = "deny"


@dataclass
class TokenPayload:
    """Decoded QToken payload."""
    sub: bytes
    iss: str
    aud: list[str]
    exp: int
    iat: int
    nbf: int
    jti: bytes
    rid: bytes
    pol: str
    ctx: bytes
    cst: dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        """Check if token is expired."""
        return time.time() > self.exp

    def is_not_yet_valid(self) -> bool:
        """Check if token is not yet valid."""
        return time.time() < self.nbf


@dataclass
class EvaluationResult:
    """Policy evaluation result."""
    effect: Effect
    matched_rule: Optional[str]
    reason: str


@dataclass
class IssuerKeys:
    """Issuer's cryptographic keys."""
    key_id: bytes
    ed25519_public_key: bytes
    mldsa_public_key: bytes
    encryption_key: bytes

    @property
    def key_id_hex(self) -> str:
        """Get key ID as hex string."""
        return self.key_id.hex()


# Try to import the Rust extension
try:
    from . import _qauth_rs as _rs
    _HAS_RUST = True
except ImportError:
    _HAS_RUST = False


class QAuthServer:
    """
    QAuth Server for token issuance and validation.

    This class handles the server-side operations of the QAuth protocol,
    including token generation and validation.
    """

    def __init__(self, issuer: str, audience: str) -> None:
        """
        Initialize a QAuth server.

        Args:
            issuer: The issuer URL (e.g., 'https://auth.example.com')
            audience: The expected audience for tokens
        """
        self.issuer = issuer
        self.audience = audience

        if _HAS_RUST:
            self._impl = _rs.QAuthServer(issuer, audience)
        else:
            # Fallback: raise error since we need the Rust implementation
            raise ImportError(
                "QAuth Rust extension not available. "
                "Please install with: pip install qauth[rust]"
            )

    def get_public_keys(self) -> IssuerKeys:
        """Get the issuer's public keys for sharing with validators."""
        keys = self._impl.get_public_keys()
        return IssuerKeys(
            key_id=keys["key_id"],
            ed25519_public_key=keys["ed25519_public_key"],
            mldsa_public_key=keys["mldsa_public_key"],
            encryption_key=keys["encryption_key"],
        )

    def create_token(
        self,
        subject: Union[str, bytes],
        policy_ref: str,
        audience: Optional[Union[str, list[str]]] = None,
        validity_seconds: int = 3600,
        client_key: Optional[bytes] = None,
        device_key: Optional[bytes] = None,
        claims: Optional[dict[str, Any]] = None,
    ) -> str:
        """
        Create a QToken.

        Args:
            subject: The subject identifier (user ID)
            policy_ref: Policy reference URN
            audience: Override audience (defaults to server's audience)
            validity_seconds: Token validity in seconds (default: 3600)
            client_key: Client's public key for binding
            device_key: Device key for binding
            claims: Custom claims to include

        Returns:
            Encoded QToken string
        """
        if isinstance(subject, str):
            subject = subject.encode("utf-8")

        aud = audience if audience is not None else self.audience
        if isinstance(aud, str):
            aud = [aud]

        return self._impl.create_token(
            subject=subject,
            issuer=self.issuer,
            audience=aud,
            policy_ref=policy_ref,
            validity_seconds=validity_seconds,
            client_key=client_key,
            device_key=device_key,
            claims=json.dumps(claims) if claims else None,
        )

    def validate_token(self, token: str) -> TokenPayload:
        """
        Validate a token and return its payload.

        Args:
            token: The QToken string to validate

        Returns:
            Decoded token payload

        Raises:
            QAuthError: If token validation fails
        """
        payload = self._impl.validate_token(token)
        return TokenPayload(
            sub=bytes.fromhex(payload["sub"]),
            iss=payload["iss"],
            aud=payload["aud"],
            exp=payload["exp"],
            iat=payload["iat"],
            nbf=payload["nbf"],
            jti=bytes.fromhex(payload["jti"]),
            rid=bytes.fromhex(payload["rid"]),
            pol=payload["pol"],
            ctx=bytes.fromhex(payload.get("ctx", "0" * 64)),
            cst=payload.get("cst", {}),
        )


class QAuthValidator:
    """
    QAuth Validator for token validation.

    Use this when you have pre-shared issuer keys and need to validate
    tokens without access to the issuer's private keys.
    """

    def __init__(
        self,
        keys: IssuerKeys,
        issuer: str,
        audience: str,
    ) -> None:
        """
        Initialize a QAuth validator.

        Args:
            keys: Issuer's public keys
            issuer: Expected issuer URL
            audience: Expected audience
        """
        if _HAS_RUST:
            self._impl = _rs.QAuthValidator(
                ed25519_public_key=keys.ed25519_public_key,
                mldsa_public_key=keys.mldsa_public_key,
                encryption_key=keys.encryption_key,
                issuer=issuer,
                audience=audience,
            )
        else:
            raise ImportError("QAuth Rust extension not available")

    def validate(self, token: str) -> TokenPayload:
        """
        Validate a token and return its payload.

        Args:
            token: The QToken string to validate

        Returns:
            Decoded token payload

        Raises:
            QAuthError: If token validation fails
        """
        payload = self._impl.validate(token)
        return TokenPayload(
            sub=bytes.fromhex(payload["sub"]),
            iss=payload["iss"],
            aud=payload["aud"],
            exp=payload["exp"],
            iat=payload["iat"],
            nbf=payload["nbf"],
            jti=bytes.fromhex(payload["jti"]),
            rid=bytes.fromhex(payload["rid"]),
            pol=payload["pol"],
            ctx=bytes.fromhex(payload.get("ctx", "0" * 64)),
            cst=payload.get("cst", {}),
        )


class QAuthClient:
    """
    QAuth Client for proof of possession.

    Use this on the client side to generate proofs of possession
    for API requests.
    """

    def __init__(self) -> None:
        """Initialize a QAuth client with a new keypair."""
        if _HAS_RUST:
            self._impl = _rs.QAuthClient()
        else:
            raise ImportError("QAuth Rust extension not available")

    @property
    def public_key(self) -> bytes:
        """Get the client's public key."""
        return self._impl.public_key

    def create_proof(
        self,
        method: str,
        uri: str,
        token: str,
        body: Optional[bytes] = None,
    ) -> str:
        """
        Create a proof of possession for an API request.

        Args:
            method: HTTP method (e.g., 'GET', 'POST')
            uri: Request URI (path + query)
            token: The QToken being used
            body: Request body (if any)

        Returns:
            Encoded proof string for X-QAuth-Proof header
        """
        return self._impl.create_proof(method, uri, token, body)


class ProofValidator:
    """
    Proof Validator for server-side proof verification.
    """

    def __init__(self, client_public_key: bytes) -> None:
        """
        Initialize a proof validator.

        Args:
            client_public_key: The client's Ed25519 public key
        """
        if _HAS_RUST:
            self._impl = _rs.ProofValidator(client_public_key)
        else:
            raise ImportError("QAuth Rust extension not available")

    def validate(
        self,
        proof: str,
        method: str,
        uri: str,
        token: str,
        body: Optional[bytes] = None,
    ) -> bool:
        """
        Validate a proof of possession.

        Args:
            proof: The proof string from X-QAuth-Proof header
            method: Expected HTTP method
            uri: Expected request URI
            token: The QToken being used
            body: Expected request body (if any)

        Returns:
            True if proof is valid

        Raises:
            QAuthError: If proof validation fails
        """
        return self._impl.validate(proof, method, uri, token, body)


class PolicyEngine:
    """
    Policy Engine for authorization decisions.

    Evaluates QAuth policies to make access control decisions.
    """

    def __init__(self) -> None:
        """Initialize a policy engine."""
        if _HAS_RUST:
            self._impl = _rs.PolicyEngine()
        else:
            raise ImportError("QAuth Rust extension not available")

    def load_policy(self, policy: dict[str, Any]) -> None:
        """
        Load a policy into the engine.

        Args:
            policy: Policy document as a dictionary
        """
        self._impl.load_policy(json.dumps(policy))

    def evaluate(
        self,
        policy_id: str,
        context: dict[str, Any],
    ) -> EvaluationResult:
        """
        Evaluate a policy for a given context.

        Args:
            policy_id: The policy ID to evaluate
            context: Evaluation context with subject, resource, request info

        Returns:
            Evaluation result with effect, matched rule, and reason
        """
        result = self._impl.evaluate(policy_id, json.dumps(context))
        result_dict = json.loads(result)
        return EvaluationResult(
            effect=Effect(result_dict["effect"]),
            matched_rule=result_dict.get("matched_rule"),
            reason=result_dict["reason"],
        )


class QAuthError(Exception):
    """Base exception for QAuth errors."""
    pass


class TokenValidationError(QAuthError):
    """Token validation failed."""
    pass


class ProofValidationError(QAuthError):
    """Proof of possession validation failed."""
    pass


class PolicyError(QAuthError):
    """Policy evaluation error."""
    pass


# Export public API
__all__ = [
    # Version info
    "__version__",
    "__protocol_version__",
    # Core classes
    "QAuthServer",
    "QAuthValidator",
    "QAuthClient",
    "ProofValidator",
    "PolicyEngine",
    # Data classes
    "TokenPayload",
    "IssuerKeys",
    "EvaluationResult",
    "Effect",
    # Exceptions
    "QAuthError",
    "TokenValidationError",
    "ProofValidationError",
    "PolicyError",
]
