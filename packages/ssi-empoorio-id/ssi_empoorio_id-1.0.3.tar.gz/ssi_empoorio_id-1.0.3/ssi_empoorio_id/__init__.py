"""
SSI Empoorio ID Python SDK
Complete implementation for SSI operations in Python
"""

__version__ = "1.0.0"
__author__ = "Empoorio Core Identity Team"

from .sdk import SSIEmporioSDK, AsyncSSIEmporioSDK, CredentialSubject, VerifiableCredential, VerificationResult
from .utils import (
    generate_uuid,
    create_credential_template,
    validate_credential_format,
    is_quantum_resistant,
    extract_credential_claims,
    format_did_document,
    create_presentation_definition,
    create_input_descriptor,
    calculate_credential_hash,
    validate_zkp_proof,
    create_status_list_entry,
    encode_status_list,
    decode_status_list
)

__all__ = [
    # Main SDK classes
    'SSIEmporioSDK',
    'AsyncSSIEmporioSDK',

    # Data structures
    'CredentialSubject',
    'VerifiableCredential',
    'VerificationResult',

    # Utility functions
    'generate_uuid',
    'create_credential_template',
    'validate_credential_format',
    'is_quantum_resistant',
    'extract_credential_claims',
    'format_did_document',
    'create_presentation_definition',
    'create_input_descriptor',
    'calculate_credential_hash',
    'validate_zkp_proof',
    'create_status_list_entry',
    'encode_status_list',
    'decode_status_list'
]
