"""
SSI Empoorio ID - Python SDK VC Manager
Verifiable Credentials management operations
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime

from .exceptions import VCError, NetworkError


class VCManager:
    """
    Verifiable Credentials Manager for SSI Empoorio ID

    Handles all VC-related operations including issuance, revocation,
    status checking, and batch operations.
    """

    def __init__(self, client):
        self.client = client

    async def issue_credential(self,
                              credential_data: Dict[str, Any],
                              options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Issue a new verifiable credential

        Args:
            credential_data: Credential data including subject, types, etc.
            options: Issuance options

        Returns:
            Issued credential

        Raises:
            VCError: If issuance fails
        """
        try:
            # Build W3C Verifiable Credential
            credential = {
                "@context": [
                    "https://www.w3.org/2018/credentials/v1",
                    "https://ssi.empoorio.id/contexts/v1"
                ],
                "type": ["VerifiableCredential", *(credential_data.get("types", []))],
                "issuer": options.get("issuerDid", self.client.config["issuer_did"]) if options else self.client.config["issuer_did"],
                "issuanceDate": datetime.now().isoformat(),
                "credentialSubject": credential_data["subject"],
                **credential_data.get("additionalFields", {})
            }

            # Add expiration if specified
            if options and options.get("expirationDate"):
                credential["expirationDate"] = options["expirationDate"]

            # Add proof
            if options and options.get("proofType"):
                credential["proof"] = await self._generate_proof(credential, options["proofType"])

            # Issue on blockchain
            result = await self.client.call_method("vcAnchor_issueCredential", [
                credential,
                options or {}
            ])

            return {
                "credential": credential,
                "transaction": result,
                "issued": True,
                "id": credential.get("id", f"vc-{result.get('hash', 'unknown')}")
            }

        except Exception as e:
            raise VCError(f"Failed to issue credential: {str(e)}")

    async def revoke_credential(self,
                               credential_id: str,
                               reason: str = "",
                               options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Revoke a verifiable credential

        Args:
            credential_id: ID of credential to revoke
            reason: Revocation reason
            options: Revocation options

        Returns:
            Revocation result

        Raises:
            VCError: If revocation fails
        """
        try:
            result = await self.client.call_method("vcAnchor_revokeCredential", [
                credential_id,
                reason,
                options or {}
            ])

            return {
                "credentialId": credential_id,
                "revoked": True,
                "reason": reason,
                "transaction": result,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            raise VCError(f"Failed to revoke credential {credential_id}: {str(e)}")

    async def suspend_credential(self,
                                credential_id: str,
                                suspension_period: int,
                                reason: str = "",
                                options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Suspend a verifiable credential temporarily

        Args:
            credential_id: ID of credential to suspend
            suspension_period: Suspension period in seconds
            reason: Suspension reason
            options: Suspension options

        Returns:
            Suspension result

        Raises:
            VCError: If suspension fails
        """
        try:
            result = await self.client.call_method("vcAnchor_suspendCredential", [
                credential_id,
                suspension_period,
                reason,
                options or {}
            ])

            return {
                "credentialId": credential_id,
                "suspended": True,
                "suspensionPeriod": suspension_period,
                "reason": reason,
                "transaction": result,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            raise VCError(f"Failed to suspend credential {credential_id}: {str(e)}")

    async def get_credential_status(self, credential_id: str) -> Dict[str, Any]:
        """
        Get the status of a verifiable credential

        Args:
            credential_id: ID of credential to check

        Returns:
            Credential status information

        Raises:
            VCError: If status check fails
        """
        try:
            result = await self.client.call_method("vcAnchor_getCredentialStatus", [
                credential_id
            ])

            if not result:
                return {
                    "credentialId": credential_id,
                    "status": "not_found",
                    "exists": False
                }

            return {
                "credentialId": credential_id,
                "status": result.get("status", "unknown"),
                "exists": True,
                "issuer": result.get("issuer"),
                "holder": result.get("holder"),
                "issuedAt": result.get("issuedAt"),
                "expiresAt": result.get("expiresAt"),
                "revokedAt": result.get("revokedAt"),
                "suspendedUntil": result.get("suspendedUntil"),
                "lastUpdated": result.get("lastUpdated")
            }

        except Exception as e:
            raise VCError(f"Failed to get credential status for {credential_id}: {str(e)}")

    async def update_credential_status(self,
                                      credential_id: str,
                                      new_status: str,
                                      options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Update the status of a verifiable credential

        Args:
            credential_id: ID of credential to update
            new_status: New status (active, revoked, suspended, expired)
            options: Update options

        Returns:
            Update result

        Raises:
            VCError: If status update fails
        """
        try:
            result = await self.client.call_method("vcAnchor_updateCredentialStatus", [
                credential_id,
                new_status,
                options or {}
            ])

            return {
                "credentialId": credential_id,
                "newStatus": new_status,
                "updated": True,
                "transaction": result,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            raise VCError(f"Failed to update credential status for {credential_id}: {str(e)}")

    async def issue_batch_credentials(self,
                                     credentials_data: List[Dict[str, Any]],
                                     options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Issue multiple verifiable credentials in batch

        Args:
            credentials_data: List of credential data
            options: Batch issuance options

        Returns:
            Batch issuance result

        Raises:
            VCError: If batch issuance fails
        """
        try:
            # Build credentials
            credentials = []
            for cred_data in credentials_data:
                credential = {
                    "@context": [
                        "https://www.w3.org/2018/credentials/v1",
                        "https://ssi.empoorio.id/contexts/v1"
                    ],
                    "type": ["VerifiableCredential", *(cred_data.get("types", []))],
                    "issuer": options.get("issuerDid", self.client.config["issuer_did"]) if options else self.client.config["issuer_did"],
                    "issuanceDate": datetime.now().isoformat(),
                    "credentialSubject": cred_data["subject"],
                    **cred_data.get("additionalFields", {})
                }
                credentials.append(credential)

            # Issue batch on blockchain
            result = await self.client.call_method("vcAnchor_issueBatchCredentials", [
                credentials,
                options or {}
            ])

            return {
                "credentials": credentials,
                "batchSize": len(credentials),
                "transaction": result,
                "issued": True,
                "batchId": result.get("batchId")
            }

        except Exception as e:
            raise VCError(f"Failed to issue batch credentials: {str(e)}")

    async def find_credentials(self,
                              query: Dict[str, Any],
                              options: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Find verifiable credentials matching criteria

        Args:
            query: Search criteria
            options: Search options

        Returns:
            List of matching credentials

        Raises:
            VCError: If search fails
        """
        try:
            result = await self.client.call_method("vcAnchor_findCredentials", [
                query,
                options or {}
            ])

            return result or []

        except Exception as e:
            raise VCError(f"Failed to find credentials: {str(e)}")

    async def get_issuer_statistics(self, issuer_did: str) -> Dict[str, Any]:
        """
        Get statistics for an issuer

        Args:
            issuer_did: Issuer DID

        Returns:
            Issuer statistics

        Raises:
            VCError: If retrieval fails
        """
        try:
            result = await self.client.call_method("vcAnchor_getIssuerStatistics", [
                issuer_did
            ])

            return result or {
                "issuerDid": issuer_did,
                "totalCredentials": 0,
                "activeCredentials": 0,
                "revokedCredentials": 0,
                "suspendedCredentials": 0
            }

        except Exception as e:
            raise VCError(f"Failed to get issuer statistics for {issuer_did}: {str(e)}")

    async def _generate_proof(self, credential: Dict[str, Any], proof_type: str) -> Dict[str, Any]:
        """
        Generate proof for credential

        Args:
            credential: Credential to sign
            proof_type: Type of proof to generate

        Returns:
            Generated proof
        """
        try:
            # This is a simplified proof generation
            # In production, this would use proper cryptographic libraries
            import hashlib
            import secrets

            credential_string = json.dumps(credential, sort_keys=True, separators=(',', ':'))
            proof_value = hashlib.sha256(credential_string.encode()).hexdigest()

            return {
                "type": proof_type,
                "created": datetime.now().isoformat(),
                "verificationMethod": f"{credential['issuer']}#keys-1",
                "proofPurpose": "assertionMethod",
                "proofValue": proof_value
            }

        except Exception as e:
            raise VCError(f"Failed to generate proof: {str(e)}")
           