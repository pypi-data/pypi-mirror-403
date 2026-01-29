"""
SSI Empoorio ID - Python SDK Client
Main client for SSI operations
"""

import asyncio
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import websockets
import aiohttp

from .exceptions import (
    SSIException, NetworkError, VerificationError,
    DIDError, VCError, ConfigurationError
)
from .did import DIDManager
from .vc import VCManager
from .verifier import Verifier
from .presenter import Presenter
from .zkp import ZKPManager
from .cross_chain import CrossChainBridge


class SSIClient:
    """
    Main SSI Empoorio ID client for Python applications

    Provides a complete interface for Self-Sovereign Identity operations
    including DID management, verifiable credentials, verification, and more.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize SSI Client

        Args:
            config: Configuration dictionary with the following keys:
                - node_url: WebSocket URL for EmpoorioChain node
                - issuer_did: Default issuer DID
                - enable_zkp: Enable ZK proofs (default: True)
                - enable_cross_chain: Enable cross-chain operations (default: True)
                - cache_enabled: Enable caching (default: True)
                - timeout: Request timeout in seconds (default: 30)
                - max_retries: Maximum retry attempts (default: 3)
        """
        self.config = {
            'node_url': 'ws://localhost:9944',
            'issuer_did': 'did:emp:python-sdk-issuer',
            'enable_zkp': True,
            'enable_cross_chain': True,
            'cache_enabled': True,
            'timeout': 30,
            'max_retries': 3,
            **(config or {})
        }

        # Initialize components
        self._websocket = None
        self._session = None
        self._connected = False

        # Initialize managers
        self.did = DIDManager(self)
        self.vc = VCManager(self)
        self.verifier = Verifier(self)
        self.presenter = Presenter(self)

        if self.config['enable_zkp']:
            self.zkp = ZKPManager(self)

        if self.config['enable_cross_chain']:
            self.cross_chain = CrossChainBridge(self)

        # Cache for responses
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes

    async def connect(self) -> None:
        """
        Connect to EmpoorioChain node

        Raises:
            NetworkError: If connection fails
        """
        try:
            # Create HTTP session for API calls
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config['timeout'])
            )

            # Connect to WebSocket for real-time updates
            self._websocket = await websockets.connect(
                self.config['node_url'],
                extra_headers=self._get_headers()
            )

            self._connected = True
            print(f"✅ Connected to SSI Empoorio ID node: {self.config['node_url']}")

        except Exception as e:
            raise NetworkError(f"Failed to connect to SSI node: {str(e)}")

    async def disconnect(self) -> None:
        """Disconnect from SSI node"""
        if self._websocket:
            await self._websocket.close()
        if self._session:
            await self._session.close()

        self._connected = False
        print("✅ Disconnected from SSI Empoorio ID node")

    async def is_connected(self) -> bool:
        """Check if client is connected"""
        return self._connected

    async def call_method(self, method: str, params: List[Any] = None) -> Dict[str, Any]:
        """
        Call a method on the SSI node

        Args:
            method: Method name
            params: Method parameters

        Returns:
            Method response

        Raises:
            NetworkError: If the call fails
        """
        if not self._connected:
            raise NetworkError("Not connected to SSI node")

        # Check cache first
        cache_key = f"{method}:{json.dumps(params or [], sort_keys=True)}"
        if self.config['cache_enabled'] and cache_key in self._cache:
            cached = self._cache[cache_key]
            if datetime.now().timestamp() - cached['timestamp'] < self._cache_ttl:
                return cached['data']

        # Prepare request
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or [],
            "id": self._generate_request_id()
        }

        # Send request with retries
        for attempt in range(self.config['max_retries']):
            try:
                await self._websocket.send(json.dumps(request))

                # Receive response
                response = await self._websocket.recv()
                result = json.loads(response)

                if 'error' in result:
                    raise SSIException(f"SSI method error: {result['error']}")

                # Cache successful response
                if self.config['cache_enabled']:
                    self._cache[cache_key] = {
                        'data': result['result'],
                        'timestamp': datetime.now().timestamp()
                    }

                return result['result']

            except Exception as e:
                if attempt == self.config['max_retries'] - 1:
                    raise NetworkError(f"SSI method call failed after {self.config['max_retries']} attempts: {str(e)}")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

    async def get_status(self) -> Dict[str, Any]:
        """
        Get SSI node status

        Returns:
            Status information
        """
        try:
            status = await self.call_method("system_health")
            return {
                "connected": True,
                "node_url": self.config['node_url'],
                "status": status,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "connected": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def get_network_stats(self) -> Dict[str, Any]:
        """
        Get network statistics

        Returns:
            Network statistics
        """
        try:
            stats = await self.call_method("system_networkState")
            return {
                "peers": stats.get("peerCount", 0),
                "best_block": stats.get("bestBlock", 0),
                "finalized_block": stats.get("finalizedBlock", 0),
                "sync_state": stats.get("syncState", "unknown")
            }
        except Exception as e:
            raise NetworkError(f"Failed to get network stats: {str(e)}")

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for WebSocket connection"""
        return {
            'User-Agent': f'SSI-Empoorio-ID-Python-SDK/{__import__(__name__.split(".")[0]).__version__}',
            'Content-Type': 'application/json'
        }

    def _generate_request_id(self) -> str:
        """Generate unique request ID"""
        import uuid
        return str(uuid.uuid4())

    def clear_cache(self) -> None:
        """Clear response cache"""
        self._cache.clear()

    def set_cache_ttl(self, ttl: int) -> None:
        """Set cache TTL in seconds"""
        self._cache_ttl = ttl

    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()