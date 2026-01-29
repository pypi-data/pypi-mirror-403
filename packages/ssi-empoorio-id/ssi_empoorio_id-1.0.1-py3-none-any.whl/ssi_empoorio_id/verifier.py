#!/usr/bin/env python3
"""
SSI Empoorio ID - Verifier Module
Handles verification of verifiable credentials and presentations
"""

import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class Verifier:
    """
    SSI Verifier for verifiable credentials and presentations
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize verifier with configuration

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
        self._vc_cache = {}
        self._presentation_cache = {}

    def verify_vc(self, vc_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify a verifiable credential

        Args:
            vc_data: Verifiable credential data

        Returns:
            Dict containing verification result with keys:
            - verified: Boolean indicating if VC is valid
            - issuer: Issuer DID
            - subject: Subject DID
            - expiration: Expiration date (if any)
            - errors: List of validation errors (if any)
        """
        try:
            logger.info(f"Verifying VC: {vc_data.get('id', 'unknown')}")

            # Basic structure validation
            if not self._validate_vc_structure(vc_data):
                return {
                    'verified': False,
                    'error': 'Invalid VC structure',
                    'issuer': None,
                    'subject': None
                }

            # Extract key information
            issuer = vc_data.get('issuer', '')
            subject = vc_data.get('credentialSubject', {}).get('id', '')
            expiration = vc_data.get('expirationDate')

            # Check expiration
            if expiration:
                try:
                    exp_datetime = datetime.fromisoformat(expiration.replace('Z', '+00:00'))
                    if exp_datetime < datetime.now(timezone.utc):
                        return {
                            'verified': False,
                            'error': 'VC has expired',
                            'issuer': issuer,
                            'subject': subject,
                            'expiration': expiration
                        }
                except ValueError:
                    return {
                        'verified': False,
                        'error': 'Invalid expiration date format',
                        'issuer': issuer,
                        'subject': subject
                    }

            # Verify issuer DID format
            if not self._validate_did_format(issuer):
                return {
                    'verified': False,
                    'error': 'Invalid issuer DID format',
                    'issuer': issuer,
                    'subject': subject
                }

            # Verify subject DID format (if present)
            if subject and not self._validate_did_format(subject):
                return {
                    'verified': False,
                    'error': 'Invalid subject DID format',
                    'issuer': issuer,
                    'subject': subject
                }

            # Check proof (simplified for this implementation)
            proof = vc_data.get('proof')
            if not proof:
                return {
                    'verified': False,
                    'error': 'Missing proof',
                    'issuer': issuer,
                    'subject': subject
                }

            # In a real implementation, this would verify cryptographic proofs
            # For now, we do basic validation
            if not self._validate_proof_structure(proof):
                return {
                    'verified': False,
                    'error': 'Invalid proof structure',
                    'issuer': issuer,
                    'subject': subject
                }

            logger.info(f"VC verification successful: {vc_data.get('id', 'unknown')}")

            return {
                'verified': True,
                'issuer': issuer,
                'subject': subject,
                'expiration': expiration,
                'proof_type': proof.get('type'),
                'verification_method': proof.get('verificationMethod')
            }

        except Exception as e:
            logger.error(f"VC verification failed: {e}")
            return {
                'verified': False,
                'error': f'Verification failed: {str(e)}',
                'issuer': vc_data.get('issuer'),
                'subject': vc_data.get('credentialSubject', {}).get('id')
            }

    def verify_presentation(self, presentation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify a verifiable presentation

        Args:
            presentation_data: Verifiable presentation data

        Returns:
            Dict containing verification result
        """
        try:
            logger.info("Verifying VP")

            # Basic structure validation
            if not self._validate_vp_structure(presentation_data):
                return {
                    'verified': False,
                    'error': 'Invalid VP structure'
                }

            # Extract information
            presentation_type = presentation_data.get('type', [])
            holder = presentation_data.get('holder')
            audience = presentation_data.get('verifiableCredential', [{}])[0].get('audience')

            # Verify holder DID format
            if holder and not self._validate_did_format(holder):
                return {
                    'verified': False,
                    'error': 'Invalid holder DID format',
                    'holder': holder
                }

            # Verify audience DID format
            if audience and not self._validate_did_format(audience):
                return {
                    'verified': False,
                    'error': 'Invalid audience DID format',
                    'audience': audience
                }

            # Verify all credentials in presentation
            credentials = presentation_data.get('verifiableCredential', [])
            verified_credentials = []

            for vc in credentials:
                vc_result = self.verify_vc(vc)
                verified_credentials.append(vc_result)

                if not vc_result['verified']:
                    return {
                        'verified': False,
                        'error': f'Invalid credential in presentation: {vc_result.get("error")}',
                        'holder': holder,
                        'audience': audience,
                        'credentials_verified': len([c for c in verified_credentials if c['verified']]),
                        'total_credentials': len(credentials)
                    }

            # Check proof
            proof = presentation_data.get('proof')
            if proof and not self._validate_proof_structure(proof):
                return {
                    'verified': False,
                    'error': 'Invalid presentation proof',
                    'holder': holder,
                    'audience': audience
                }

            logger.info("VP verification successful")

            return {
                'verified': True,
                'holder': holder,
                'audience': audience,
                'presentation_type': presentation_type,
                'credentials_verified': len(verified_credentials),
                'total_credentials': len(credentials)
            }

        except Exception as e:
            logger.error(f"VP verification failed: {e}")
            return {
                'verified': False,
                'error': f'Verification failed: {str(e)}'
            }

    def _validate_vc_structure(self, vc_data: Dict[str, Any]) -> bool:
        """Validate basic VC structure"""
        required_fields = ['@context', 'type', 'issuer', 'issuanceDate', 'credentialSubject']
        return all(field in vc_data for field in required_fields)

    def _validate_vp_structure(self, vp_data: Dict[str, Any]) -> bool:
        """Validate basic VP structure"""
        required_fields = ['@context', 'type', 'verifiableCredential']
        return all(field in vp_data for field in required_fields)

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

    def _validate_proof_structure(self, proof: Dict[str, Any]) -> bool:
        """Validate proof structure"""
        if not proof or not isinstance(proof, dict):
            return False

        required_proof_fields = ['type', 'created', 'verificationMethod', 'proofPurpose']
        return all(field in proof for field in required_proof_fields)

    def batch_verify_vc(self, vc_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Batch verify multiple VCs

        Args:
            vc_list: List of VC data dictionaries

        Returns:
            List of verification results
        """
        results = []
        for vc in vc_list:
            result = self.verify_vc(vc)
            results.append(result)

        return results

    def get_verification_status(self, vc_id: str) -> Dict[str, Any]:
        """
        Get verification status for a VC

        Args:
            vc_id: VC ID to check

        Returns:
            Status information
        """
        # In a real implementation, this would check against a registry
        return {
            'vc_id': vc_id,
            'status': 'valid',
            'last_checked': datetime.now(timezone.utc).isoformat(),
            'next_check': (datetime.now(timezone.utc).replace(hour=2, minute=0, second=0, microsecond=0)).isoformat()
        }


# Convenience functions for backward compatibility
def verify_vc(vc_data: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Convenience function to verify a single VC"""
    verifier = Verifier(config or {})
    return verifier.verify_vc(vc_data)


def verify_presentation(presentation_data: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Convenience function to verify a presentation"""
    verifier = Verifier(config or {})
    return verifier.verify_presentation(presentation_data)