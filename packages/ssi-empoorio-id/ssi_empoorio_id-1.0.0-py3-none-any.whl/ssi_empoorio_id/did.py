"""
SSI Empoorio ID - Python SDK DID Manager
DID (Decentralized Identifier) management operations
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime

from .exceptions import DIDError, NetworkError


class DIDManager:
    """
    DID Manager for SSI Empoorio ID

    Handles all DID-related operations including creation, resolution,
    updating, and deactivation of decentralized identifiers.
    """

    def __init__(self, client):
        self.client = client

    async def create_did(self,
                        controller: str,
                        verification_methods: List[Dict[str, Any]] = None,
                        services: List[Dict[str, Any]] = None,
                        options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Create a new DID

        Args:
            controller: DID controller address
            verification_methods: List of verification methods
            services: List of DID services
            options: Additional options

        Returns:
            Created DID document

        Raises:
            DIDError: If DID creation fails
        """
        try:
            # Generate DID
            did = f"did:emp:{controller}"

            # Default verification methods
            if not verification_methods:
                verification_methods = [{
                    "id": f"{did}#keys-1",
                    "controller": did,
                    "methodType": "Ed25519VerificationKey2020",
                    "publicKey": self._generate_public_key(),
                    "blockchainAccountId": controller
                }]

            # Default services
            if not services:
                services = []

            # Create DID document
            did_document = {
                "id": did,
                "controller": [did],
                "verificationMethods": verification_methods,
                "authentication": [f"{did}#keys-1"],
                "assertionMethod": [f"{did}#keys-1"],
                "keyAgreement": [],
                "capabilityInvocation": [],
                "service": services,
                "created": datetime.now().isoformat(),
                "updated": datetime.now().isoformat(),
                "version": 1
            }

            # Register on blockchain
            result = await self.client.call_method("didRegistry_registerDid", [
                did,
                did_document,
                options or {}
            ])

            return {
                "did": did,
                "document": did_document,
                "transaction": result,
                "created": True
            }

        except Exception as e:
            raise DIDError(f"Failed to create DID: {str(e)}")

    async def resolve_did(self, did: str) -> Optional[Dict[str, Any]]:
        """
        Resolve a DID to its document

        Args:
            did: DID to resolve

        Returns:
            DID document or None if not found

        Raises:
            DIDError: If resolution fails
        """
        try:
            result = await self.client.call_method("didRegistry_resolveDid", [did])

            if not result:
                return None

            return result

        except Exception as e:
            raise DIDError(f"Failed to resolve DID {did}: {str(e)}")

    async def update_did(self,
                        did: str,
                        updates: Dict[str, Any],
                        options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Update a DID document

        Args:
            did: DID to update
            updates: Updates to apply
            options: Update options

        Returns:
            Update result

        Raises:
            DIDError: If update fails
        """
        try:
            # Get current document
            current_doc = await self.resolve_did(did)
            if not current_doc:
                raise DIDError(f"DID {did} not found")

            # Apply updates
            updated_doc = {**current_doc, **updates}
            updated_doc["updated"] = datetime.now().isoformat()
            updated_doc["version"] = current_doc.get("version", 1) + 1

            # Update on blockchain
            result = await self.client.call_method("didRegistry_updateDid", [
                did,
                updated_doc,
                options or {}
            ])

            return {
                "did": did,
                "updated": True,
                "version": updated_doc["version"],
                "transaction": result
            }

        except Exception as e:
            raise DIDError(f"Failed to update DID {did}: {str(e)}")

    async def deactivate_did(self, did: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Deactivate a DID

        Args:
            did: DID to deactivate
            options: Deactivation options

        Returns:
            Deactivation result

        Raises:
            DIDError: If deactivation fails
        """
        try:
            result = await self.client.call_method("didRegistry_deactivateDid", [
                did,
                options or {}
            ])

            return {
                "did": did,
                "deactivated": True,
                "transaction": result
            }

        except Exception as e:
            raise DIDError(f"Failed to deactivate DID {did}: {str(e)}")

    async def add_verification_method(self,
                                     did: str,
                                     method: Dict[str, Any],
                                     options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Add a verification method to a DID

        Args:
            did: Target DID
            method: Verification method to add
            options: Additional options

        Returns:
            Update result

        Raises:
            DIDError: If addition fails
        """
        try:
            result = await self.client.call_method("didRegistry_addVerificationMethod", [
                did,
                method,
                options or {}
            ])

            return {
                "did": did,
                "methodAdded": method["id"],
                "transaction": result
            }

        except Exception as e:
            raise DIDError(f"Failed to add verification method to DID {did}: {str(e)}")

    async def remove_verification_method(self,
                                        did: str,
                                        method_id: str,
                                        options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Remove a verification method from a DID

        Args:
            did: Target DID
            method_id: ID of method to remove
            options: Additional options

        Returns:
            Update result

        Raises:
            DIDError: If removal fails
        """
        try:
            result = await self.client.call_method("didRegistry_removeVerificationMethod", [
                did,
                method_id,
                options or {}
            ])

            return {
                "did": did,
                "methodRemoved": method_id,
                "transaction": result
            }

        except Exception as e:
            raise DIDError(f"Failed to remove verification method from DID {did}: {str(e)}")

    async def add_service(self,
                         did: str,
                         service: Dict[str, Any],
                         options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Add a service to a DID

        Args:
            did: Target DID
            service: Service to add
            options: Additional options

        Returns:
            Update result

        Raises:
            DIDError: If addition fails
        """
        try:
            result = await self.client.call_method("didRegistry_addService", [
                did,
                service,
                options or {}
            ])

            return {
                "did": did,
                "serviceAdded": service["id"],
                "transaction": result
            }

        except Exception as e:
            raise DIDError(f"Failed to add service to DID {did}: {str(e)}")

    async def find_by_controller(self, controller: str) -> List[str]:
        """
        Find DIDs by controller

        Args:
            controller: Controller address

        Returns:
            List of DIDs controlled by the address

        Raises:
            DIDError: If search fails
        """
        try:
            result = await self.client.call_method("didRegistry_findByController", [controller])
            return result or []

        except Exception as e:
            raise DIDError(f"Failed to find DIDs by controller {controller}: {str(e)}")

    async def find_by_verification_method(self, method_id: str) -> Optional[str]:
        """
        Find DID by verification method

        Args:
            method_id: Verification method ID

        Returns:
            DID that contains the method or None

        Raises:
            DIDError: If search fails
        """
        try:
            result = await self.client.call_method("didRegistry_findByVerificationMethod", [method_id])
            return result

        except Exception as e:
            raise DIDError(f"Failed to find DID by verification method {method_id}: {str(e)}")

    async def get_did_history(self, did: str) -> List[Dict[str, Any]]:
        """
        Get DID update history

        Args:
            did: Target DID

        Returns:
            List of DID updates

        Raises:
            DIDError: If retrieval fails
        """
        try:
            result = await self.client.call_method("didRegistry_getHistory", [did])
            return result or []

        except Exception as e:
            raise DIDError(f"Failed to get DID history for {did}: {str(e)}")

    async def validate_did_format(self, did: str) -> bool:
        """
        Validate DID format

        Args:
            did: DID to validate

        Returns:
            True if valid format
        """
        # Basic validation for did:emp: format
        if not did.startswith("did:emp:"):
            return False

        if len(did) <= 8:  # "did:emp:" is 8 chars
            return False

        # Check for valid characters
        import re
        remaining = did[8:]  # After "did:emp:"
        return bool(re.match(r'^[a-zA-Z0-9\-_\.]+$', remaining))

    def _generate_public_key(self) -> str:
        """
        Generate a mock public key for demonstration
        In production, this would use proper cryptographic libraries
        """
        import secrets
        return secrets.token_hex(32)

    async def get_did_statistics(self) -> Dict[str, Any]:
        """
        Get DID registry statistics

        Returns:
            Statistics about the DID registry

        Raises:
            DIDError: If retrieval fails
        """
        try:
            result = await self.client.call_method("didRegistry_getStatistics")
            return result or {}

        except Exception as e:
            raise DIDError(f"Failed to get DID statistics: {str(e)}")