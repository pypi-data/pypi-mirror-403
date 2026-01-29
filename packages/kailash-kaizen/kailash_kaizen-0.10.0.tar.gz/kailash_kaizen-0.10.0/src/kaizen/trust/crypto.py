"""
EATP Cryptographic Utilities.

Provides Ed25519 signing and verification for trust chain integrity.
Uses PyNaCl for cryptographic operations.
"""

import base64
import hashlib
import json
from dataclasses import asdict, is_dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Tuple, Union

try:
    from nacl.exceptions import BadSignatureError
    from nacl.signing import SigningKey, VerifyKey

    NACL_AVAILABLE = True
except ImportError:
    NACL_AVAILABLE = False
    SigningKey = None
    VerifyKey = None
    BadSignatureError = Exception

from kaizen.trust.exceptions import InvalidSignatureError


def generate_keypair() -> Tuple[str, str]:
    """
    Generate an Ed25519 key pair for signing.

    Returns:
        Tuple of (private_key_base64, public_key_base64)

    Raises:
        ImportError: If PyNaCl is not installed

    Example:
        >>> private_key, public_key = generate_keypair()
        >>> len(private_key) > 0
        True
    """
    if not NACL_AVAILABLE:
        raise ImportError(
            "PyNaCl is required for cryptographic operations. "
            "Install with: pip install pynacl"
        )

    signing_key = SigningKey.generate()
    private_key_bytes = bytes(signing_key)
    public_key_bytes = bytes(signing_key.verify_key)

    return (
        base64.b64encode(private_key_bytes).decode("utf-8"),
        base64.b64encode(public_key_bytes).decode("utf-8"),
    )


def sign(payload: Union[bytes, str, dict], private_key: str) -> str:
    """
    Sign a payload with Ed25519 private key.

    Args:
        payload: Data to sign (bytes, string, or dict)
        private_key: Base64-encoded private key

    Returns:
        Base64-encoded signature

    Raises:
        ImportError: If PyNaCl is not installed
        ValueError: If private key is invalid

    Example:
        >>> private_key, public_key = generate_keypair()
        >>> signature = sign({"action": "test"}, private_key)
        >>> len(signature) > 0
        True
    """
    if not NACL_AVAILABLE:
        raise ImportError(
            "PyNaCl is required for cryptographic operations. "
            "Install with: pip install pynacl"
        )

    # Convert payload to bytes
    if isinstance(payload, dict):
        payload_bytes = serialize_for_signing(payload).encode("utf-8")
    elif isinstance(payload, str):
        payload_bytes = payload.encode("utf-8")
    else:
        payload_bytes = payload

    # Decode private key
    try:
        private_key_bytes = base64.b64decode(private_key)
        signing_key = SigningKey(private_key_bytes)
    except Exception as e:
        raise ValueError(f"Invalid private key: {e}")

    # Sign
    signed = signing_key.sign(payload_bytes)
    signature = signed.signature

    return base64.b64encode(signature).decode("utf-8")


def verify_signature(
    payload: Union[bytes, str, dict], signature: str, public_key: str
) -> bool:
    """
    Verify an Ed25519 signature.

    Args:
        payload: Original data that was signed
        signature: Base64-encoded signature
        public_key: Base64-encoded public key

    Returns:
        True if signature is valid, False otherwise

    Raises:
        ImportError: If PyNaCl is not installed
        InvalidSignatureError: If signature verification fails with error

    Example:
        >>> private_key, public_key = generate_keypair()
        >>> signature = sign("test", private_key)
        >>> verify_signature("test", signature, public_key)
        True
        >>> verify_signature("tampered", signature, public_key)
        False
    """
    if not NACL_AVAILABLE:
        raise ImportError(
            "PyNaCl is required for cryptographic operations. "
            "Install with: pip install pynacl"
        )

    # Convert payload to bytes
    if isinstance(payload, dict):
        payload_bytes = serialize_for_signing(payload).encode("utf-8")
    elif isinstance(payload, str):
        payload_bytes = payload.encode("utf-8")
    else:
        payload_bytes = payload

    try:
        # Decode signature and public key
        signature_bytes = base64.b64decode(signature)
        public_key_bytes = base64.b64decode(public_key)
        verify_key = VerifyKey(public_key_bytes)

        # Verify
        verify_key.verify(payload_bytes, signature_bytes)
        return True

    except BadSignatureError:
        return False
    except Exception as e:
        raise InvalidSignatureError(f"Signature verification error: {e}")


def serialize_for_signing(obj: Any) -> str:
    """
    Serialize an object for signing in a deterministic way.

    Converts dataclasses, dicts, and other types to a canonical JSON string
    that will produce the same output for equivalent inputs.

    Args:
        obj: Object to serialize (dataclass, dict, or primitive)

    Returns:
        Canonical JSON string

    Example:
        >>> serialize_for_signing({"b": 2, "a": 1})
        '{"a":1,"b":2}'
    """

    def convert(item: Any) -> Any:
        """Recursively convert objects to JSON-serializable types."""
        if is_dataclass(item) and not isinstance(item, type):
            return convert(asdict(item))
        elif isinstance(item, dict):
            return {k: convert(v) for k, v in sorted(item.items())}
        elif isinstance(item, (list, tuple)):
            return [convert(i) for i in item]
        elif isinstance(item, datetime):
            return item.isoformat()
        elif isinstance(item, Enum):
            return item.value
        elif isinstance(item, bytes):
            return base64.b64encode(item).decode("utf-8")
        else:
            return item

    converted = convert(obj)
    return json.dumps(converted, separators=(",", ":"), sort_keys=True)


def hash_chain(data: Union[str, dict, bytes]) -> str:
    """
    Compute SHA-256 hash of data for trust chain integrity.

    Args:
        data: Data to hash (string, dict, or bytes)

    Returns:
        Hex-encoded SHA-256 hash

    Example:
        >>> hash_chain({"id": "test"})
        'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'[:64]
    """
    if isinstance(data, dict):
        data_bytes = serialize_for_signing(data).encode("utf-8")
    elif isinstance(data, str):
        data_bytes = data.encode("utf-8")
    else:
        data_bytes = data

    return hashlib.sha256(data_bytes).hexdigest()


def hash_trust_chain_state(
    genesis_id: str, capability_ids: list, delegation_ids: list, constraint_hash: str
) -> str:
    """
    Compute hash of current trust chain state.

    This hash changes when any component of the trust chain changes,
    enabling quick verification of chain integrity.

    Args:
        genesis_id: ID of the genesis record
        capability_ids: List of capability attestation IDs
        delegation_ids: List of delegation record IDs
        constraint_hash: Hash of constraint envelope

    Returns:
        Hex-encoded SHA-256 hash of trust chain state

    Example:
        >>> hash_trust_chain_state("gen-001", ["cap-001"], [], "abc123")
        # Returns deterministic hash
    """
    state = {
        "genesis_id": genesis_id,
        "capability_ids": sorted(capability_ids),
        "delegation_ids": sorted(delegation_ids),
        "constraint_hash": constraint_hash,
    }
    return hash_chain(state)
