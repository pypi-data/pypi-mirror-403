# QAuth - Post-Quantum Authentication for Python

[![PyPI version](https://badge.fury.io/py/qauth.svg)](https://badge.fury.io/py/qauth)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Next-generation authentication protocol designed to replace OAuth 2.0 and JWT with post-quantum security.

## Installation

```bash
# Using pip
pip install qauth

# Using pip3
pip3 install qauth

# Using pipx (for CLI tools)
pipx install qauth

# Using poetry
poetry add qauth

# Using pdm
pdm add qauth

# Using uv
uv pip install qauth
```

## Quick Start

```python
from qauth import QAuthServer, QAuthClient, PolicyEngine

# Create a server instance
server = QAuthServer(
    issuer="https://auth.example.com",
    audience="https://api.example.com"
)

# Create an access token
token = server.create_token(
    subject="user-123",
    policy_ref="urn:qauth:policy:default",
    validity_seconds=3600,
    claims={
        "email": "user@example.com",
        "roles": ["user", "premium"],
    },
)

# Validate a token
payload = server.validate_token(token)
print(f"Subject: {payload.sub.decode()}")
print(f"Expires: {payload.exp}")
```

## Client-Side Usage

```python
from qauth import QAuthClient

# Create a client instance (generates a new keypair)
client = QAuthClient()

# Get the client's public key (send to server during auth)
public_key = client.public_key

# Create proof of possession for API requests
proof = client.create_proof("GET", "/api/resource", token)

# Make API request with token and proof
import requests
response = requests.get(
    "https://api.example.com/resource",
    headers={
        "Authorization": f"QAuth {token}",
        "X-QAuth-Proof": proof,
    },
)
```

## Server-Side Validation

```python
from qauth import QAuthValidator, ProofValidator

# Create a validator with pre-shared issuer keys
validator = QAuthValidator(
    keys=issuer_keys,
    issuer="https://auth.example.com",
    audience="https://api.example.com",
)

# Validate token
try:
    payload = validator.validate(token)
    print(f"Token valid for user: {payload.sub}")
except Exception as e:
    print(f"Token validation failed: {e}")

# Validate proof of possession
proof_validator = ProofValidator(client_public_key)
try:
    proof_validator.validate(proof, "GET", "/api/resource", token)
    print("Proof valid")
except Exception as e:
    print(f"Proof validation failed: {e}")
```

## Policy-Based Authorization

```python
from qauth import PolicyEngine, Effect

engine = PolicyEngine()

# Load a policy
engine.load_policy({
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
            "id": "admin-only",
            "effect": "allow",
            "resources": ["admin/**"],
            "actions": ["*"],
            "conditions": {
                "custom": {
                    "role": {"in": ["admin"]},
                },
            },
        },
    ],
})

# Evaluate authorization
result = engine.evaluate(
    "urn:qauth:policy:api-access",
    {
        "subject": {
            "id": "user-123",
            "attributes": {"role": "user"},
        },
        "resource": {
            "path": "projects/456",
        },
        "request": {
            "action": "read",
        },
    },
)

if result.effect == Effect.ALLOW:
    print("Access granted")
else:
    print(f"Access denied: {result.reason}")
```

## FastAPI Integration

```python
from fastapi import FastAPI, Depends, HTTPException, Header
from qauth import QAuthValidator, ProofValidator, IssuerKeys

app = FastAPI()

# Configure validator
validator = QAuthValidator(
    keys=issuer_keys,
    issuer="https://auth.example.com",
    audience="https://api.example.com",
)

async def verify_qauth(
    authorization: str = Header(...),
    x_qauth_proof: str = Header(...),
):
    if not authorization.startswith("QAuth "):
        raise HTTPException(401, "Invalid authorization header")

    token = authorization[6:]

    try:
        payload = validator.validate(token)
    except Exception as e:
        raise HTTPException(401, f"Invalid token: {e}")

    # In production, also verify the proof

    return payload

@app.get("/api/resource")
async def get_resource(payload = Depends(verify_qauth)):
    return {"user": payload.sub.decode()}
```

## API Reference

### QAuthServer

Server-side class for token creation and validation.

```python
server = QAuthServer(issuer: str, audience: str)

# Get public keys for sharing with validators
keys = server.get_public_keys() -> IssuerKeys

# Create a token
token = server.create_token(
    subject: str | bytes,
    policy_ref: str,
    audience: str | list[str] | None = None,
    validity_seconds: int = 3600,
    client_key: bytes | None = None,
    device_key: bytes | None = None,
    claims: dict[str, Any] | None = None,
) -> str

# Validate a token
payload = server.validate_token(token: str) -> TokenPayload
```

### QAuthClient

Client-side class for proof of possession.

```python
client = QAuthClient()

# Get client's public key
public_key = client.public_key -> bytes

# Create proof for API request
proof = client.create_proof(
    method: str,
    uri: str,
    token: str,
    body: bytes | None = None,
) -> str
```

### PolicyEngine

Evaluate authorization policies.

```python
engine = PolicyEngine()

# Load a policy
engine.load_policy(policy: dict[str, Any]) -> None

# Evaluate authorization
result = engine.evaluate(
    policy_id: str,
    context: dict[str, Any],
) -> EvaluationResult
```

## Data Classes

```python
@dataclass
class TokenPayload:
    sub: bytes        # Subject identifier
    iss: str          # Issuer
    aud: list[str]    # Audiences
    exp: int          # Expiration time
    iat: int          # Issued at
    nbf: int          # Not before
    jti: bytes        # Token ID
    rid: bytes        # Revocation ID
    pol: str          # Policy reference
    ctx: bytes        # Context hash
    cst: dict         # Custom claims

@dataclass
class EvaluationResult:
    effect: Effect
    matched_rule: str | None
    reason: str

class Effect(Enum):
    ALLOW = "allow"
    DENY = "deny"
```

## Requirements

- Python 3.9+
- cryptography >= 41.0.0
- pynacl >= 1.5.0

## Why QAuth over JWT?

| JWT/OAuth Problem | QAuth Solution |
|-------------------|----------------|
| Algorithm confusion attacks | Server-enforced, no client selection |
| Bearer tokens can be stolen | Proof-of-possession mandatory |
| No built-in revocation | Instant revocation system |
| Payload visible (base64) | Encrypted with XChaCha20-Poly1305 |
| Single signature | Dual: Ed25519 + ML-DSA-65 |
| No post-quantum security | ML-DSA-65 (NIST FIPS 204) |

## Related Packages

- **Rust**: `cargo add qauth`
- **TypeScript/Node.js**: `npm install @qauth/sdk`
- **Go**: `go get github.com/tushar-agrawal/qauth`

## License

MIT License - [LICENSE](LICENSE)

## Author

Tushar Agrawal - [tusharagrawal.in](https://tusharagrawal.in)

## Links

- [Documentation](https://tusharagrawal.in/qauth)
- [GitHub Repository](https://github.com/Tushar010402/Tushar-Agrawal-Website)
- [Changelog](https://github.com/Tushar010402/Tushar-Agrawal-Website/blob/master/quantum-shield/qauth/CHANGELOG.md)
