"""
SSI Empoorio ID - Python SDK Exceptions
Custom exceptions for SSI operations
"""


class SSIException(Exception):
    """Base exception for SSI operations"""
    pass


class NetworkError(SSIException):
    """Network-related errors"""
    pass


class VerificationError(SSIException):
    """Credential or presentation verification errors"""
    pass


class DIDError(SSIException):
    """DID-related errors"""
    pass


class VCError(SSIException):
    """Verifiable Credential errors"""
    pass


class ZKPError(SSIException):
    """Zero-Knowledge Proof errors"""
    pass


class CrossChainError(SSIException):
    """Cross-chain operation errors"""
    pass


class ConfigurationError(SSIException):
    """Configuration-related errors"""
    pass


class AuthenticationError(SSIException):
    """Authentication and authorization errors"""
    pass


class ValidationError(SSIException):
    """Data validation errors"""
    pass