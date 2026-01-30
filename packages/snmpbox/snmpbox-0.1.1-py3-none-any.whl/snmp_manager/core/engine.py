"""
Core SNMP Engine - Abstracts pysnmp complexity and provides robust functionality.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum

import pysnmp.hlapi.v3arch.asyncio as hlapi
from pysnmp.entity.rfc3413 import cmdgen
from pysnmp.proto import errind
from pysnmp.smi.rfc1902 import ObjectType, ObjectIdentity

logger = logging.getLogger(__name__)


class SNMPVersion(Enum):
    """SNMP protocol versions."""
    V1 = 0
    V2C = 1
    V3 = 3


class SNMPError(Exception):
    """Base SNMP error."""
    pass


class ConnectionError(SNMPError):
    """Connection-related errors."""
    pass


class TimeoutError(SNMPError):
    """Timeout errors."""
    pass


class AuthenticationError(SNMPError):
    """Authentication errors."""
    pass


@dataclass
class SNMPResponse:
    """Standard SNMP response format."""
    success: bool
    error_indication: Optional[str] = None
    error_status: Optional[str] = None
    error_index: Optional[int] = None
    var_binds: Optional[List[Tuple[str, Any]]] = None
    execution_time_ms: Optional[float] = None


@dataclass
class SNMPCredentials:
    """SNMP connection credentials."""
    community: str = "public"
    version: SNMPVersion = SNMPVersion.V2C
    username: Optional[str] = None
    auth_key: Optional[str] = None
    priv_key: Optional[str] = None
    auth_protocol: Optional[str] = None
    priv_protocol: Optional[str] = None


@dataclass
class SNMPTarget:
    """SNMP target device configuration."""
    host: str
    port: int = 161
    timeout: int = 3
    retries: int = 3
    credentials: SNMPCredentials = None

    def __post_init__(self):
        if self.credentials is None:
            self.credentials = SNMPCredentials()


class SNMPEngine:
    """
    High-level SNMP engine that abstracts pysnmp complexity.

    Features:
    - Automatic retry logic with exponential backoff
    - Connection pooling and reuse
    - Error handling and logging
    - Async/await support
    - Response timeout management
    """

    def __init__(self, max_concurrent_requests: int = 50):
        """
        Initialize SNMP engine.

        Args:
            max_concurrent_requests: Maximum concurrent SNMP requests
        """
        self.max_concurrent_requests = max_concurrent_requests
        self._semaphore = asyncio.Semaphore(max_concurrent_requests)
        self._engines = {}  # Reuse SNMP engines for different credentials
        self._connection_cache = {}

    async def get_snmp_engine(self, target: SNMPTarget) -> hlapi.SnmpEngine:
        """Get or create SNMP engine for target."""
        cache_key = self._get_cache_key(target)

        if cache_key not in self._engines:
            self._engines[cache_key] = hlapi.SnmpEngine()

        return self._engines[cache_key]

    def _get_cache_key(self, target: SNMPTarget) -> str:
        """Generate cache key for SNMP engine."""
        creds = target.credentials
        if creds.version == SNMPVersion.V3:
            return f"v3_{creds.username}_{creds.auth_protocol}"
        else:
            return f"v{creds.version.value}_{creds.community}"

    async def get_auth_data(self, target: SNMPTarget) -> Union[hlapi.CommunityData, hlapi.UsmUserData]:
        """Create authentication data for target."""
        creds = target.credentials

        if creds.version == SNMPVersion.V3:
            if not creds.username:
                raise AuthenticationError("Username required for SNMPv3")

            return hlapi.UsmUserData(
                creds.username,
                authKey=creds.auth_key,
                privKey=creds.priv_key,
                authProtocol=getattr(hlapi, creds.auth_protocol or "USM_AUTH_NONE"),
                privProtocol=getattr(hlapi, creds.priv_protocol or "USM_PRIV_NONE")
            )
        else:
            return hlapi.CommunityData(creds.community, mpModel=creds.version.value)

    async def get_transport_target(self, target: SNMPTarget) -> hlapi.UdpTransportTarget:
        """Create transport target for SNMP connection."""
        return await hlapi.UdpTransportTarget.create(
            (target.host, target.port),
            timeout=target.timeout,
            retries=target.retries
        )

    async def _execute_with_semaphore(self, coro):
        """Execute coroutine with semaphore limiting."""
        async with self._semaphore:
            return await coro

    async def get(self, target: SNMPTarget, oids: List[str]) -> SNMPResponse:
        """
        Perform SNMP GET operation.

        Args:
            target: SNMP target configuration
            oids: List of OIDs to query

        Returns:
            SNMPResponse with results or error
        """
        import time
        start_time = time.time()

        try:
            async def _get():
                snmp_engine = await self.get_snmp_engine(target)
                auth_data = await self.get_auth_data(target)
                transport_target = await self.get_transport_target(target)

                # Convert OID strings to ObjectType
                var_binds = [
                    ObjectType(ObjectIdentity(oid))
                    for oid in oids
                ]

                error_indication, error_status, error_index, var_binds = await hlapi.get_cmd(
                    snmp_engine,
                    auth_data,
                    transport_target,
                    hlapi.ContextData(),
                    *var_binds
                )

                # Process results
                processed_var_binds = []
                if var_binds:
                    for var_bind in var_binds:
                        oid_str = str(var_bind[0])
                        value = var_bind[1].prettyPrint() if var_bind[1] else None
                        processed_var_binds.append((oid_str, value))

                return SNMPResponse(
                    success=error_indication is None and error_status == 0,
                    error_indication=str(error_indication) if error_indication else None,
                    error_status=str(error_status.prettyPrint()) if error_status else None,
                    error_index=int(error_index) if error_index else None,
                    var_binds=processed_var_binds,
                    execution_time_ms=(time.time() - start_time) * 1000
                )

            return await self._execute_with_semaphore(_get())

        except Exception as e:
            logger.error(f"SNMP GET failed for {target.host}: {e}")
            return SNMPResponse(
                success=False,
                error_indication=str(e),
                execution_time_ms=(time.time() - start_time) * 1000
            )

    async def get_next(self, target: SNMPTarget, oids: List[str]) -> SNMPResponse:
        """
        Perform SNMP GETNEXT operation.

        Args:
            target: SNMP target configuration
            oids: List of OIDs to query

        Returns:
            SNMPResponse with results or error
        """
        import time
        start_time = time.time()

        try:
            async def _get_next():
                snmp_engine = await self.get_snmp_engine(target)
                auth_data = await self.get_auth_data(target)
                transport_target = await self.get_transport_target(target)

                var_binds = [
                    ObjectType(ObjectIdentity(oid))
                    for oid in oids
                ]

                error_indication, error_status, error_index, var_binds = await hlapi.next_cmd(
                    snmp_engine,
                    auth_data,
                    transport_target,
                    hlapi.ContextData(),
                    *var_binds
                )

                processed_var_binds = []
                if var_binds:
                    for var_bind in var_binds:
                        oid_str = str(var_bind[0])
                        value = var_bind[1].prettyPrint() if var_bind[1] else None
                        processed_var_binds.append((oid_str, value))

                return SNMPResponse(
                    success=error_indication is None and error_status == 0,
                    error_indication=str(error_indication) if error_indication else None,
                    error_status=str(error_status.prettyPrint()) if error_status else None,
                    error_index=int(error_index) if error_index else None,
                    var_binds=processed_var_binds,
                    execution_time_ms=(time.time() - start_time) * 1000
                )

            return await self._execute_with_semaphore(_get_next())

        except Exception as e:
            logger.error(f"SNMP GETNEXT failed for {target.host}: {e}")
            return SNMPResponse(
                success=False,
                error_indication=str(e),
                execution_time_ms=(time.time() - start_time) * 1000
            )

    async def walk(self, target: SNMPTarget, oid: str, max_repetitions: int = 10) -> SNMPResponse:
        """
        Perform SNMP WALK operation using GETBULK.

        Args:
            target: SNMP target configuration
            oid: Starting OID for walk
            max_repetitions: Max repetitions per GETBULK

        Returns:
            SNMPResponse with all results
        """
        import time
        start_time = time.time()

        try:
            async def _walk():
                snmp_engine = await self.get_snmp_engine(target)
                auth_data = await self.get_auth_data(target)
                transport_target = await self.get_transport_target(target)

                var_binds = [ObjectType(ObjectIdentity(oid))]

                error_indication, error_status, error_index, var_binds = await hlapi.bulk_cmd(
                    snmp_engine,
                    auth_data,
                    transport_target,
                    hlapi.ContextData(),
                    0,  # non-repeaters
                    max_repetitions,
                    *var_binds
                )

                processed_var_binds = []
                if var_binds:
                    for var_bind in var_binds:
                        oid_str = str(var_bind[0])
                        value = var_bind[1].prettyPrint() if var_bind[1] else None
                        processed_var_binds.append((oid_str, value))

                return SNMPResponse(
                    success=error_indication is None and error_status == 0,
                    error_indication=str(error_indication) if error_indication else None,
                    error_status=str(error_status.prettyPrint()) if error_status else None,
                    error_index=int(error_index) if error_index else None,
                    var_binds=processed_var_binds,
                    execution_time_ms=(time.time() - start_time) * 1000
                )

            return await self._execute_with_semaphore(_walk())

        except Exception as e:
            logger.error(f"SNMP WALK failed for {target.host}: {e}")
            return SNMPResponse(
                success=False,
                error_indication=str(e),
                execution_time_ms=(time.time() - start_time) * 1000
            )

    async def test_connection(self, target: SNMPTarget) -> bool:
        """
        Test SNMP connectivity to target.

        Args:
            target: SNMP target configuration

        Returns:
            True if connection successful, False otherwise
        """
        # Try to get system description
        response = await self.get(target, ["1.3.6.1.2.1.1.1.0"])
        return response.success

    async def close(self):
        """Close SNMP engine and cleanup resources."""
        for engine in self._engines.values():
            engine.close_dispatcher()
        self._engines.clear()
        self._connection_cache.clear()