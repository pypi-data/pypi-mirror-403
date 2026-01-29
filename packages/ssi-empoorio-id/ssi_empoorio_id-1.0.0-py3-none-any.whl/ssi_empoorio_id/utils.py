"""
SSI Empoorio ID Python SDK Utilities
"""

import uuid
from typing import Dict, Any, List
from datetime import datetime


def generate_uuid() -> str:
    """
    Generate a random UUID for credential IDs

    Returns:
        UUID string
    """
    return str(uuid.uuid4())


def create_credential_template(
    subject: Dict[str, Any],
    issuer: str,
    credential_type: List[str] = None
) -> Dict[str, Any]:
    """
    Create a basic credential template

    Args:
        subject: Credential subject data
        issuer: Issuer DID
        credential_type: List of credential types

    Returns:
        Credential template dictionary
    """
    if credential_type is None:
        credential_type = ["VerifiableCredential"]

    return {
        "@context": [
            "https://www.w3.org/2018/credentials/v1",
            "https://schemas.empoorio.id/kyc-basic/v1"
        ],
        "type": credential_type,
        "issuer": issuer,
        "issuanceDate": datetime.utcnow().isoformat() + "Z",
        "credentialSubject": subject
    }


def validate_credential_format(credential: Dict[str, Any]) -> bool:
    """
    Validate credential format

    Args:
        credential: Credential to validate

    Returns:
        True if valid format
    """
    required_fields = ["@context", "type", "issuer", "issuanceDate", "credentialSubject"]

    # Check required fields
    for field in required_fields:
        if field not in credential:
            return False

    # Validate @context
    if not isinstance(credential["@context"], list) and not isinstance(credential["@context"], str):
        return False

    # Validate type
    if not isinstance(credential["type"], list):
        return False

    return True


def is_quantum_resistant(proof_type: str) -> bool:
    """
    Check if proof type is quantum-resistant

    Args:
        proof_type: Proof type to check

    Returns:
        True if quantum-resistant
    """
    quantum_proofs = [
        'Dilithium', 'Falcon', 'HybridEd25519Dilithium',
        'Kyber', 'QuantumResistant'
    ]
    return any(qp in proof_type for qp in quantum_proofs)


def extract_credential_claims(credential: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract claims from credential subject

    Args:
        credential: Credential to extract from

    Returns:
        Claims dictionary
    """
    subject = credential.get("credentialSubject", {})
    if isinstance(subject, dict):
        claims = subject.copy()
        claims.pop('id', None)
        return claims
    return {}


def format_did_document(did: str, public_keys: List[Dict[str, Any]] = None,
                       services: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Format a DID document

    Args:
        did: DID identifier
        public_keys: List of public keys
        services: List of services

    Returns:
        DID document
    """
    document = {
        "@context": "https://www.w3.org/ns/did/v1",
        "id": did,
        "verificationMethod": public_keys or [],
        "service": services or []
    }

    return document


def create_presentation_definition(
    name: str,
    purpose: str,
    input_descriptors: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Create a presentation definition for OIDC4VP

    Args:
        name: Presentation definition name
        purpose: Purpose description
        input_descriptors: Input descriptors

    Returns:
        Presentation definition
    """
    return {
        "id": generate_uuid(),
        "name": name,
        "purpose": purpose,
        "input_descriptors": input_descriptors
    }


def create_input_descriptor(
    id: str,
    name: str,
    purpose: str,
    schema: Dict[str, Any],
    constraints: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Create an input descriptor for presentation definition

    Args:
        id: Descriptor ID
        name: Descriptor name
        purpose: Purpose description
        schema: JSON schema
        constraints: Additional constraints

    Returns:
        Input descriptor
    """
    descriptor = {
        "id": id,
        "name": name,
        "purpose": purpose,
        "schema": schema
    }

    if constraints:
        descriptor["constraints"] = constraints

    return descriptor


def calculate_credential_hash(credential: Dict[str, Any]) -> str:
    """
    Calculate credential hash for anchoring

    Args:
        credential: Credential to hash

    Returns:
        Hex hash string
    """
    import hashlib
    import json

    # Create canonical JSON
    canonical = json.dumps(credential, sort_keys=True, separators=(',', ':'))

    # Hash with SHA-256
    hash_obj = hashlib.sha256(canonical.encode('utf-8'))
    return '0x' + hash_obj.hexdigest()


def validate_zkp_proof(proof: Dict[str, Any], public_inputs: Dict[str, Any]) -> bool:
    """
    Validate ZKP proof (simplified)

    Args:
        proof: ZKP proof
        public_inputs: Public inputs

    Returns:
        True if valid
    """
    # This is a simplified validation - in production, this would use
    # proper ZKP verification libraries
    required_fields = ['type', 'proof', 'publicValue']

    for field in required_fields:
        if field not in proof:
            return False

    # Basic structure validation
    if 'proof' not in proof or 't' not in proof['proof'] or 's' not in proof['proof']:
        return False

    return True


def create_status_list_entry(index: int, status: str = 'valid') -> Dict[str, Any]:
    """
    Create a status list entry

    Args:
        index: Entry index
        status: Status ('valid', 'revoked', 'suspended')

    Returns:
        Status list entry
    """
    return {
        "id": f"urn:status:{index}",
        "type": "StatusList2021Entry",
        "statusPurpose": "revocation",
        "statusListIndex": str(index),
        "statusListCredential": f"urn:status-list:{index // 1000}"
    }


def encode_status_list(entries: List[Dict[str, Any]]) -> str:
    """
    Encode status list as compressed bitstring

    Args:
        entries: Status list entries

    Returns:
        Base64 encoded compressed bitstring
    """
    import base64
    import zlib

    # Create bit array (simplified - in production use proper bit manipulation)
    bit_string = '0' * len(entries)

    # Convert to bytes and compress
    bit_bytes = bit_string.encode('utf-8')
    compressed = zlib.compress(bit_bytes)

    return base64.b64encode(compressed).decode('utf-8')


def decode_status_list(encoded_list: str, index: int) -> str:
    """
    Decode status from compressed bitstring

    Args:
        encoded_list: Base64 encoded compressed bitstring
        index: Index to check

    Returns:
        Status ('valid', 'revoked', 'suspended')
    """
    import base64
    import zlib

    try:
        # Decode and decompress
        compressed = base64.b64decode(encoded_list)
        bit_string = zlib.decompress(compressed).decode('utf-8')

        # Check bit at index (simplified)
        if index < len(bit_string):
            return 'revoked' if bit_string[index] == '1' else 'valid'
        else:
            return 'valid'
    except Exception:
        return 'unknown'