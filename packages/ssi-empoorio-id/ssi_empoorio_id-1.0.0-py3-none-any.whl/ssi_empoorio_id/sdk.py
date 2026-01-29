"""
SSI Empoorio ID Python SDK
Complete implementation for SSI operations
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict

import aiohttp
import requests


@dataclass
class CredentialSubject:
    """Credential subject data structure"""
    id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Proof:
    """Cryptographic proof structure"""
    type: str
    created: str
    verificationMethod: str
    proofPurpose: str
    proofValue: str
    quantumResistant: Optional[bool] = None
    zkpEnabled: Optional[bool] = None


@dataclass
class CredentialStatus:
    """Credential status information"""
    id: str
    type: str
    statusPurpose: str
    statusListIndex: str
    statusListCredential: str


@dataclass
class VerifiableCredential:
    """Verifiable Credential structure"""
    context: List[str]
    id: str
    type: List[str]
    issuer: str
    issuanceDate: str
    credentialSubject: CredentialSubject
    expirationDate: Optional[str] = None
    proof: Optional[Proof] = None
    credentialStatus: Optional[CredentialStatus] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['@context'] = data.pop('context')
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VerifiableCredential':
        # Handle @context
        if '@context' in data:
            data['context'] = data.pop('@context')
            if isinstance(data['context'], str):
                data['context'] = [data['context']]

        # Convert credentialSubject to CredentialSubject if it's a dict
        if isinstance(data.get('credentialSubject'), dict):
            data['credentialSubject'] = CredentialSubject(**data['credentialSubject'])

        return cls(**data)


@dataclass
class VerifiablePresentation:
    """Verifiable Presentation structure"""
    context: List[str]
    type: List[str]
    verifiableCredential: Optional[List[VerifiableCredential]] = None
    holder: Optional[str] = None
    proof: Optional[Proof] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['@context'] = data.pop('context')
        return data


@dataclass
class IssuerOptions:
    """Options for credential issuance"""
    selectiveDisclosure: Optional[bool] = None
    revealedIndices: Optional[List[int]] = None
    ageVerification: Optional[bool] = None
    minimumAge: Optional[int] = None
    zkpEnabled: Optional[bool] = None
    quantumResistant: Optional[bool] = None
    expirationDate: Optional[str] = None


@dataclass
class VerificationResult:
    """Result of credential verification"""
    verified: bool
    checks: Optional[Dict[str, bool]] = None
    errors: Optional[List[str]] = None
    warnings: Optional[List[str]] = None


class SSIEmporioSDK:
    """
    Complete SSI Empoorio ID SDK for Python applications
    """

    def __init__(
        self,
        issuer_url: str = "http://localhost:3001",
        verifier_url: str = "http://localhost:3002",
        api_key: Optional[str] = None,
        timeout: float = 30.0,
        session: Optional[requests.Session] = None
    ):
        """
        Initialize the SSI SDK

        Args:
            issuer_url: URL of the issuer API
            verifier_url: URL of the verifier API
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds
            session: Optional requests session to reuse
        """
        self.issuer_url = issuer_url.rstrip('/')
        self.verifier_url = verifier_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout

        # HTTP session management
        self._session = session or requests.Session()
        self._session.timeout = timeout

        # Set default headers
        self._session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': f'SSI-Empoorio-SDK-Python/{__import__("ssi_empoorio_id").__version__}'
        })

        if api_key:
            self._session.headers['Authorization'] = f'Bearer {api_key}'

    def _make_request(
        self,
        method: str,
        url: str,
        json_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Make HTTP request with error handling"""
        try:
            response = self._session.request(
                method=method.upper(),
                url=url,
                json=json_data,
                **kwargs
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"HTTP request failed: {str(e)}")

    # ============================================================================
    # ISSUER OPERATIONS
    # ============================================================================

    def issue_credential(
        self,
        subject: Union[CredentialSubject, Dict[str, Any]],
        credential_type: Optional[List[str]] = None,
        options: Optional[IssuerOptions] = None
    ) -> VerifiableCredential:
        """
        Issue a single verifiable credential

        Args:
            subject: Credential subject data
            credential_type: List of credential types
            options: Issuance options

        Returns:
            VerifiableCredential: The issued credential
        """
        if isinstance(subject, dict):
            subject = CredentialSubject(**subject)

        payload = {
            "credentialSubject": subject.to_dict(),
            "type": credential_type or ["VerifiableCredential"],
            "holderDid": subject.id,
        }

        if options:
            payload.update(asdict(options))

        response = self._make_request(
            "POST",
            f"{self.issuer_url}/api/v1/issuer/vc/issue",
            payload
        )

        return VerifiableCredential.from_dict(response["vc"])

    def issue_credentials_batch(
        self,
        credentials: List[Dict[str, Any]],
        options: Optional[IssuerOptions] = None
    ) -> List[VerifiableCredential]:
        """
        Issue multiple verifiable credentials in batch

        Args:
            credentials: List of credential data
            options: Issuance options

        Returns:
            List of issued credentials
        """
        payload = {
            "credentials": [
                {
                    "credentialSubject": cred["credentialSubject"],
                    "type": cred.get("type", ["VerifiableCredential"]),
                    "expirationDate": cred.get("expirationDate"),
                    "holderDid": cred["credentialSubject"].get("id")
                }
                for cred in credentials
            ]
        }

        if options:
            payload.update(asdict(options))

        response = self._make_request(
            "POST",
            f"{self.issuer_url}/api/v1/issuer/vc/batch-issue",
            payload
        )

        return [VerifiableCredential.from_dict(vc) for vc in response["vcs"]]

    def revoke_credential(self, vc_id: str, reason: Optional[str] = None) -> Dict[str, Any]:
        """
        Revoke a verifiable credential

        Args:
            vc_id: Credential ID to revoke
            reason: Optional revocation reason

        Returns:
            Revocation result
        """
        payload = {"vcId": vc_id}
        if reason:
            payload["reason"] = reason

        return self._make_request(
            "POST",
            f"{self.issuer_url}/api/v1/issuer/vc/revoke",
            payload
        )

    def get_credential_status(self, vc_id: str) -> Dict[str, str]:
        """
        Get credential status

        Args:
            vc_id: Credential ID to check

        Returns:
            Status information
        """
        return self._make_request(
            "GET",
            f"{self.issuer_url}/api/v1/issuer/vc/status/{vc_id}"
        )

    # ============================================================================
    # VERIFIER OPERATIONS
    # ============================================================================

    def verify_credential(
        self,
        credential: Union[VerifiableCredential, Dict[str, Any]],
        options: Optional[Dict[str, Any]] = None
    ) -> VerificationResult:
        """
        Verify a single verifiable credential

        Args:
            credential: Credential to verify
            options: Verification options

        Returns:
            VerificationResult: Verification result
        """
        if isinstance(credential, VerifiableCredential):
            credential = credential.to_dict()

        payload = {
            "verifiableCredential": credential,
            "options": options or {}
        }

        response = self._make_request(
            "POST",
            f"{self.verifier_url}/api/v1/verification/vc",
            payload
        )

        return VerificationResult(**response["result"])

    def verify_credentials_batch(
        self,
        credentials: List[Union[VerifiableCredential, Dict[str, Any]]],
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Verify multiple credentials in batch

        Args:
            credentials: List of credentials to verify
            options: Verification options

        Returns:
            Batch verification results
        """
        verifiable_credentials = []
        for cred in credentials:
            if isinstance(cred, VerifiableCredential):
                verifiable_credentials.append(cred.to_dict())
            else:
                verifiable_credentials.append(cred)

        payload = {
            "verifiableCredentials": verifiable_credentials,
            "options": options or {}
        }

        return self._make_request(
            "POST",
            f"{self.verifier_url}/api/v1/verification/vc/batch",
            payload
        )

    def verify_presentation(
        self,
        presentation: Union[VerifiablePresentation, Dict[str, Any]],
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Verify a verifiable presentation

        Args:
            presentation: Presentation to verify
            options: Verification options

        Returns:
            Verification result
        """
        if isinstance(presentation, VerifiablePresentation):
            presentation = presentation.to_dict()

        payload = {
            "verifiablePresentation": presentation,
            "options": options or {}
        }

        return self._make_request(
            "POST",
            f"{self.verifier_url}/api/v1/presentation/vp",
            payload
        )

    def request_presentation(
        self,
        presentation_definition: Dict[str, Any],
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Request a presentation from a holder (OIDC4VP)

        Args:
            presentation_definition: Presentation definition
            options: Request options

        Returns:
            Presentation request data
        """
        payload = {
            "presentationDefinition": presentation_definition,
            **(options or {})
        }

        return self._make_request(
            "POST",
            f"{self.verifier_url}/api/v1/presentation/request",
            payload
        )

    def get_presentation_definitions(self) -> Dict[str, Any]:
        """
        Get available presentation definition templates

        Returns:
            Available presentation definitions
        """
        return self._make_request(
            "GET",
            f"{self.verifier_url}/api/v1/presentation/definitions"
        )

    def get_verification_policies(self) -> Dict[str, Any]:
        """
        Get verification policies

        Returns:
            Verification policies
        """
        return self._make_request(
            "GET",
            f"{self.verifier_url}/api/v1/verification/policies"
        )

    # ============================================================================
    # STATUS REGISTRY OPERATIONS
    # ============================================================================

    def update_credential_status(
        self,
        credential_id: str,
        status: str,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update credential status

        Args:
            credential_id: Credential to update
            status: New status ('revoked', 'suspended', 'active')
            reason: Optional reason

        Returns:
            Update result
        """
        payload = {
            "credentialId": credential_id,
            "credentialStatus": status
        }
        if reason:
            payload["statusReason"] = reason

        return self._make_request(
            "POST",
            f"{self.issuer_url}/api/v1/status/update",
            payload
        )

    def get_status_list(self, list_id: str) -> Dict[str, Any]:
        """
        Get status list credential

        Args:
            list_id: Status list ID

        Returns:
            Status list credential
        """
        return self._make_request(
            "GET",
            f"{self.issuer_url}/api/v1/status/list/{list_id}"
        )

    def check_status_in_list(self, list_id: str, index: int) -> Dict[str, Any]:
        """
        Check specific credential status in list

        Args:
            list_id: Status list ID
            index: Credential index in list

        Returns:
            Status information
        """
        return self._make_request(
            "GET",
            f"{self.issuer_url}/api/v1/status/check/{list_id}/{index}"
        )

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================

    def create_test_did(self, prefix: str = "emp") -> str:
        """
        Create a DID for testing

        Args:
            prefix: DID prefix

        Returns:
            Generated DID
        """
        random_id = str(uuid.uuid4())[:8]
        return f"did:{prefix}:{random_id}"

    def validate_did(self, did: str) -> bool:
        """
        Validate DID format

        Args:
            did: DID to validate

        Returns:
            True if valid
        """
        import re
        did_regex = r"^did:[a-z0-9]+:.+$"
        return bool(re.match(did_regex, did))

    def is_credential_expired(self, credential: VerifiableCredential) -> bool:
        """
        Check if credential is expired

        Args:
            credential: Credential to check

        Returns:
            True if expired
        """
        if not credential.expirationDate:
            return False
        return datetime.fromisoformat(credential.expirationDate.replace('Z', '+00:00')) < datetime.now()

    def extract_claims(self, credential: VerifiableCredential) -> Dict[str, Any]:
        """
        Extract claims from credential subject

        Args:
            credential: Credential to extract from

        Returns:
            Claims dictionary
        """
        subject_dict = credential.credentialSubject.to_dict()
        subject_dict.pop('id', None)
        return subject_dict

    def get_issuer_did(self, credential: VerifiableCredential) -> str:
        """
        Get issuer DID from credential

        Args:
            credential: Credential to get issuer from

        Returns:
            Issuer DID
        """
        return credential.issuer

    def get_subject_did(self, credential: VerifiableCredential) -> str:
        """
        Get subject DID from credential

        Args:
            credential: Credential to get subject from

        Returns:
            Subject DID
        """
        return credential.credentialSubject.id or ""

    def close(self):
        """Close the HTTP session"""
        self._session.close()


# Async version of the SDK
class AsyncSSIEmporioSDK:
    """
    Asynchronous version of the SSI Empoorio ID SDK
    """

    def __init__(
        self,
        issuer_url: str = "http://localhost:3001",
        verifier_url: str = "http://localhost:3002",
        api_key: Optional[str] = None,
        timeout: float = 30.0
    ):
        self.issuer_url = issuer_url.rstrip('/')
        self.verifier_url = verifier_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout

        # HTTP headers
        self.headers = {
            'Content-Type': 'application/json',
            'User-Agent': f'SSI-Empoorio-SDK-Python-Async/{__import__("ssi_empoorio_id").__version__}'
        }
        if api_key:
            self.headers['Authorization'] = f'Bearer {api_key}'

    async def _make_request(
        self,
        method: str,
        url: str,
        json_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Make async HTTP request"""
        async with aiohttp.ClientSession(headers=self.headers, timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
            async with session.request(method.upper(), url, json=json_data, **kwargs) as response:
                response.raise_for_status()
                return await response.json()

    async def issue_credential(
        self,
        subject: Union[CredentialSubject, Dict[str, Any]],
        credential_type: Optional[List[str]] = None,
        options: Optional[IssuerOptions] = None
    ) -> VerifiableCredential:
        """Async version of issue_credential"""
        if isinstance(subject, dict):
            subject = CredentialSubject(**subject)

        payload = {
            "credentialSubject": subject.to_dict(),
            "type": credential_type or ["VerifiableCredential"],
            "holderDid": subject.id,
        }

        if options:
            payload.update(asdict(options))

        response = await self._make_request(
            "POST",
            f"{self.issuer_url}/api/v1/issuer/vc/issue",
            payload
        )

        return VerifiableCredential.from_dict(response["vc"])

    # Add other async methods as needed...


# Export both sync and async versions
__all__ = ['SSIEmporioSDK', 'AsyncSSIEmporioSDK', 'CredentialSubject', 'VerifiableCredential', 'VerificationResult']