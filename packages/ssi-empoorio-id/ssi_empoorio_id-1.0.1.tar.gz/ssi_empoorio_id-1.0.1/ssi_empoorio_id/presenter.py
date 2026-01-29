#!/usr/bin/env python3
"""
SSI Empoorio ID - Presenter Module
Handles presentation creation and management for verifiable credentials
"""

import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class Presenter:
    """
    SSI Presenter for creating and managing verifiable presentations
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize presenter with configuration

        Args:
            config: Configuration dictionary containing:
                - node_url: Substrate node URL
                - api_base_url: API base URL
                - timeout: Request timeout
                - cache_enabled: Whether to use caching
        """
        self.config = config
        self.node_url = config.get('node_url', 'ws://localhost:9944')
        self.api_base_url = config.get('api_base_url', 'http://localhost:3001')
        self.timeout = config.get('timeout', 30)
        self.cache_enabled = config.get('cache_enabled', True)

        # Initialize caches
        self._presentation_cache = {}

    def create_presentation(self, credentials: List[Dict[str, Any]],
                          holder_did: str,
                          audience: Optional[str] = None,
                          domain: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a verifiable presentation from credentials

        Args:
            credentials: List of verifiable credentials
            holder_did: DID of the presentation holder
            audience: Intended audience for the presentation
            domain: Domain for the presentation

        Returns:
            Dict containing the verifiable presentation
        """
        try:
            logger.info(f"Creating presentation for holder: {holder_did}")

            # Validate inputs
            if not self._validate_did_format(holder_did):
                raise ValueError(f"Invalid holder DID format: {holder_did}")

            if audience and not self._validate_did_format(audience):
                raise ValueError(f"Invalid audience DID format: {audience}")

            # Create presentation structure
            presentation = {
                '@context': [
                    'https://www.w3.org/2018/credentials/v1',
                    'https://www.w3.org/2018/credentials/examples/v1'
                ],
                'type': ['VerifiablePresentation'],
                'verifiableCredential': credentials,
                'holder': holder_did,
                'created': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
            }

            # Add optional fields
            if audience:
                presentation['audience'] = audience

            if domain:
                presentation['domain'] = domain

            # Create proof
            proof = self._create_presentation_proof(presentation, holder_did)
            presentation['proof'] = proof

            logger.info(f"Presentation created successfully for holder: {holder_did}")

            return presentation

        except Exception as e:
            logger.error(f"Presentation creation failed: {e}")
            raise

    def selective_disclosure(self, credential: Dict[str, Any],
                           disclosed_claims: List[str]) -> Dict[str, Any]:
        """
        Create a selectively disclosed version of a credential

        Args:
            credential: Original verifiable credential
            disclosed_claims: List of claim names to disclose

        Returns:
            Dict containing the selectively disclosed credential
        """
        try:
            logger.info("Creating selective disclosure")

            # Create a copy of the credential
            disclosed_credential = credential.copy()

            # Get the credential subject
            subject = disclosed_credential.get('credentialSubject', {})

            # Filter claims based on disclosed_claims
            if isinstance(subject, dict):
                filtered_subject = {}

                # Always include id if present
                if 'id' in subject:
                    filtered_subject['id'] = subject['id']

                # Include only disclosed claims
                for claim in disclosed_claims:
                    if claim in subject:
                        filtered_subject[claim] = subject[claim]

                disclosed_credential['credentialSubject'] = filtered_subject

            # Update proof to reflect selective disclosure
            if 'proof' in disclosed_credential:
                disclosed_credential['proof'] = self._update_proof_for_selective_disclosure(
                    disclosed_credential['proof'], disclosed_claims
                )

            logger.info("Selective disclosure created successfully")

            return disclosed_credential

        except Exception as e:
            logger.error(f"Selective disclosure failed: {e}")
            raise

    def batch_present(self, credential_sets: List[List[Dict[str, Any]]],
                     holder_did: str,
                     audience: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Create multiple presentations in batch

        Args:
            credential_sets: List of credential sets for presentations
            holder_did: DID of the presentation holder
            audience: Intended audience for presentations

        Returns:
            List of verifiable presentations
        """
        presentations = []

        for credentials in credential_sets:
            try:
                presentation = self.create_presentation(
                    credentials, holder_did, audience
                )
                presentations.append(presentation)
            except Exception as e:
                logger.error(f"Failed to create presentation in batch: {e}")
                # Continue with other presentations

        return presentations

    def get_presentation_metadata(self, presentation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract metadata from a presentation

        Args:
            presentation: Verifiable presentation

        Returns:
            Dict containing presentation metadata
        """
        metadata = {
            'holder': presentation.get('holder'),
            'audience': presentation.get('audience'),
            'domain': presentation.get('domain'),
            'created': presentation.get('created'),
            'credential_count': len(presentation.get('verifiableCredential', [])),
            'type': presentation.get('type', [])
        }

        # Extract credential types
        credentials = presentation.get('verifiableCredential', [])
        credential_types = set()

        for cred in credentials:
            if isinstance(cred, dict) and 'type' in cred:
                if isinstance(cred['type'], list):
                    credential_types.update(cred['type'])
                else:
                    credential_types.add(cred['type'])

        metadata['credential_types'] = list(credential_types)

        return metadata

    def _validate_did_format(self, did: str) -> bool:
        """Validate DID format"""
        if not did or not isinstance(did, str):
            return False

        # Basic DID format validation
        if not did.startswith('did:'):
            return False

        parts = did.split(':')
        if len(parts) < 3:
            return False

        # For SSI Empoorio, we expect did:emp: format
        if parts[0] != 'did' or parts[1] != 'emp':
            return False

        # Check identifier format (basic validation)
        identifier = parts[2]
        if not identifier or len(identifier) > 256:
            return False

        # Allow alphanumeric, hyphens, underscores, dots
        allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.')

        return all(c in allowed_chars for c in identifier)

    def _create_presentation_proof(self, presentation: Dict[str, Any], holder_did: str) -> Dict[str, Any]:
        """
        Create a proof for the presentation

        Args:
            presentation: The presentation to create proof for
            holder_did: DID of the holder

        Returns:
            Dict containing the proof
        """
        # In a real implementation, this would create a cryptographic proof
        # For now, we create a basic proof structure
        return {
            'type': 'Ed25519Signature2020',
            'created': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
            'verificationMethod': f'{holder_did}#keys-1',
            'proofPurpose': 'authentication',
            'proofValue': 'z3sW...'  # Placeholder for actual signature
        }

    def _update_proof_for_selective_disclosure(self, original_proof: Dict[str, Any],
                                             disclosed_claims: List[str]) -> Dict[str, Any]:
        """
        Update proof for selective disclosure

        Args:
            original_proof: Original proof
            disclosed_claims: List of disclosed claims

        Returns:
            Updated proof
        """
        # In a real implementation, this would update the proof to reflect selective disclosure
        # For now, we return a modified proof
        updated_proof = original_proof.copy()
        updated_proof['disclosedClaims'] = disclosed_claims
        updated_proof['proofPurpose'] = 'selectiveDisclosure'

        return updated_proof


# Convenience functions for backward compatibility
def create_presentation(credentials: List[Dict[str, Any]], holder_did: str,
                       audience: Optional[str] = None, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Convenience function to create a presentation"""
    presenter = Presenter(config or {})
    return presenter.create_presentation(credentials, holder_did, audience)


def selective_disclosure(credential: Dict[str, Any], disclosed_claims: List[str],
                        config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Convenience function for selective disclosure"""
    presenter = Presenter(config or {})
    return presenter.selective_disclosure(credential, disclosed_claims)