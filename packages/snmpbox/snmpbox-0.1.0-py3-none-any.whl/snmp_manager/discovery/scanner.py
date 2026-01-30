"""
Network Scanner - Discovers SNMP-enabled devices on network.
"""

import asyncio
import ipaddress
import logging
from typing import List, Optional, Set, Tuple
from concurrent.futures import ThreadPoolExecutor
import socket

from ..core.engine import SNMPEngine, SNMPTarget, SNMPVersion

logger = logging.getLogger(__name__)


class NetworkScanner:
    """
    High-performance network scanner for discovering SNMP-enabled devices.

    Features:
    - Concurrent scanning with configurable concurrency
    - Support for multiple network ranges
    - ARP table scanning for local network discovery
    - SNMP protocol detection
    - Port scanning for SNMP services
    """

    def __init__(self, max_concurrent_scans: int = 100, timeout: float = 2.0):
        """
        Initialize network scanner.

        Args:
            max_concurrent_scans: Maximum concurrent scan operations
            timeout: Connection timeout in seconds
        """
        self.max_concurrent_scans = max_concurrent_scans
        self.timeout = timeout
        self.snmp_engine = SNMPEngine(max_concurrent_requests=max_concurrent_scans)
        self._semaphore = asyncio.Semaphore(max_concurrent_scans)

    async def scan_network_range(
        self,
        network_range: str,
        ports: List[int] = None,
        communities: List[str] = None
    ) -> List[dict]:
        """
        Scan network range for SNMP-enabled devices.

        Args:
            network_range: Network range in CIDR format (e.g., "192.168.1.0/24")
            ports: List of ports to scan (default: [161, 162])
            communities: List of SNMP communities to try (default common ones)

        Returns:
            List of discovered device information
        """
        if ports is None:
            ports = [161, 162]

        if communities is None:
            communities = ["public", "private", "community", "snmp", "admin"]

        logger.info(f"Scanning network range: {network_range}")

        # Generate IP addresses from network range
        network = ipaddress.ip_network(network_range, strict=False)
        ip_addresses = [str(ip) for ip in network.hosts()]

        logger.info(f"Generated {len(ip_addresses)} IP addresses to scan")

        # Scan IPs concurrently
        tasks = []
        for ip in ip_addresses:
            for port in ports:
                task = self._scan_host_port(ip, port, communities)
                tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter successful results
        discovered_devices = []
        for result in results:
            if isinstance(result, dict) and result:
                discovered_devices.append(result)

        logger.info(f"Discovered {len(discovered_devices)} SNMP-enabled devices")
        return discovered_devices

    async def _scan_host_port(
        self,
        ip: str,
        port: int,
        communities: List[str]
    ) -> Optional[dict]:
        """Scan specific host and port for SNMP services."""
        async with self._semaphore:
            try:
                # First check if port is open
                if not await self._is_port_open(ip, port):
                    return None

                # Try SNMP with different communities
                for community in communities:
                    target = SNMPTarget(
                        host=ip,
                        port=port,
                        timeout=self.timeout,
                        credentials=SNMPTarget().credentials  # Will be set below
                    )
                    target.credentials.community = community
                    target.credentials.version = SNMPVersion.V2C

                    try:
                        # Test SNMP connection
                        if await self.snmp_engine.test_connection(target):
                            # Get basic device info
                            device_info = await self._get_basic_device_info(target)
                            device_info.update({
                                "ip": ip,
                                "port": port,
                                "community": community,
                                "discovery_method": "snmp_scan"
                            })
                            return device_info

                    except Exception as e:
                        logger.debug(f"SNMP failed for {ip}:{port} with community '{community}': {e}")
                        continue

                return None

            except Exception as e:
                logger.debug(f"Scan failed for {ip}:{port}: {e}")
                return None

    async def _is_port_open(self, host: str, port: int) -> bool:
        """Check if specific port is open on host."""
        try:
            # Use asyncio.to_thread for blocking socket operations
            def check_port():
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(self.timeout)
                result = sock.connect_ex((host, port))
                sock.close()
                return result == 0

            return await asyncio.to_thread(check_port)
        except Exception:
            return False

    async def _get_basic_device_info(self, target: SNMPTarget) -> dict:
        """Get basic device information via SNMP."""
        device_info = {
            "snmp_accessible": True,
            "system": {},
            "interfaces": [],
            "vendor": None,
            "model": None,
            "description": None,
            "uptime": None
        }

        try:
            # System information OIDs
            system_oids = [
                ("1.3.6.1.2.1.1.1.0", "description"),      # System description
                ("1.3.6.1.2.1.1.3.0", "uptime"),          # System uptime
                ("1.3.6.1.2.1.1.5.0", "name"),            # System name
                ("1.3.6.1.2.1.1.6.0", "location"),        # System location
                ("1.3.6.1.2.1.1.4.0", "contact"),         # System contact
            ]

            # Get system info
            oid_list = [oid for oid, _ in system_oids]
            response = await self.snmp_engine.get(target, oid_list)

            if response.success and response.var_binds:
                for oid_str, value in response.var_binds:
                    # Find corresponding field name
                    field_name = None
                    for oid_pattern, name in system_oids:
                        if oid_str.startswith(oid_pattern):
                            field_name = name
                            break

                    if field_name and value:
                        device_info["system"][field_name] = value

                        # Extract vendor and model from description
                        if field_name == "description":
                            device_info["description"] = value
                            vendor, model = self._parse_device_description(value)
                            if vendor:
                                device_info["vendor"] = vendor
                            if model:
                                device_info["model"] = model

            # Get interface count
            if_response = await self.snmp_engine.get(target, ["1.3.6.1.2.1.2.1.0"])
            if if_response.success and if_response.var_binds:
                interface_count = if_response.var_binds[0][1]
                try:
                    device_info["interface_count"] = int(interface_count)
                except ValueError:
                    pass

            # Try to identify device type via enterprise OID
            enterprise_response = await self.snmp_engine.get(target, ["1.3.6.1.2.1.1.2.0"])
            if enterprise_response.success and enterprise_response.var_binds:
                enterprise_oid = enterprise_response.var_binds[0][1]
                device_info["enterprise_oid"] = enterprise_oid

                # Try to identify vendor from enterprise OID
                vendor_from_oid = self._identify_vendor_from_enterprise_oid(enterprise_oid)
                if vendor_from_oid and not device_info.get("vendor"):
                    device_info["vendor"] = vendor_from_oid

        except Exception as e:
            logger.error(f"Failed to get device info from {target.host}: {e}")
            device_info["snmp_accessible"] = False

        return device_info

    def _parse_device_description(self, description: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Parse device description to extract vendor and model.

        Args:
            description: System description from SNMP

        Returns:
            Tuple of (vendor, model)
        """
        description_lower = description.lower()

        # Vendor patterns
        vendor_patterns = {
            "huawei": ["huawei", "h3c", "hpe"],
            "zte": ["zte", "zhongxing"],
            "cisco": ["cisco", "ios"],
            "juniper": ["juniper", "junos"],
            "vsol": ["vsol", "vision"],
            "fiberhome": ["fiberhome", "an5506"],
            "nokia": ["nokia", "alcatel"],
            "ericsson": ["ericsson"],
            "mikrotik": ["mikrotik", "routeros"],
        }

        vendor = None
        for detected_vendor, patterns in vendor_patterns.items():
            if any(pattern in description_lower for pattern in patterns):
                vendor = detected_vendor
                break

        # Model extraction (simplified)
        model = None
        if vendor:
            # Try to extract model after vendor name
            vendor_pos = description_lower.find(vendor)
            if vendor_pos != -1:
                remaining = description[vendor_pos + len(vendor):].strip()
                # Take first few words as model
                model_parts = remaining.split()[:3]
                model = " ".join(model_parts).strip(" ,.-_")

        return vendor, model

    def _identify_vendor_from_enterprise_oid(self, enterprise_oid: str) -> Optional[str]:
        """
        Identify vendor from enterprise OID.

        Args:
            enterprise_oid: Enterprise OID string

        Returns:
            Vendor name or None
        """
        # Known enterprise OID prefixes
        enterprise_map = {
            "1.3.6.1.4.1.2011": "huawei",
            "1.3.6.1.4.1.3902": "zte",
            "1.3.6.1.4.1.9": "cisco",
            "1.3.6.1.4.1.2636": "juniper",
            "1.3.6.1.4.1.94": "nokia",
            "1.3.6.1.4.1.193": "ericsson",
            "1.3.6.1.4.1.14988": "mikrotik",
        }

        for oid_prefix, vendor in enterprise_map.items():
            if enterprise_oid.startswith(oid_prefix):
                return vendor

        return None

    async def scan_arp_table(self) -> List[str]:
        """
        Scan ARP table to discover local network devices.

        Returns:
            List of IP addresses from ARP table
        """
        try:
            def read_arp_table():
                arp_entries = []
                try:
                    import platform
                    system = platform.system().lower()

                    if system == "linux":
                        with open("/proc/net/arp", "r") as f:
                            for line in f.readlines()[1:]:  # Skip header
                                parts = line.split()
                                if len(parts) >= 4 and parts[2] == "0x2":  # Complete entry
                                    arp_entries.append(parts[0])
                    elif system == "windows":
                        import subprocess
                        result = subprocess.run(["arp", "-a"], capture_output=True, text=True)
                        for line in result.stdout.split('\n'):
                            if "dynamic" in line.lower():
                                parts = line.split()
                                if len(parts) >= 2:
                                    arp_entries.append(parts[1].strip("()"))
                    elif system == "darwin":  # macOS
                        import subprocess
                        result = subprocess.run(["arp", "-a"], capture_output=True, text=True)
                        for line in result.stdout.split('\n'):
                            if "(" in line and ")" in line:
                                start = line.find("(") + 1
                                end = line.find(")")
                                ip = line[start:end]
                                arp_entries.append(ip)

                except Exception as e:
                    logger.error(f"Failed to read ARP table: {e}")

                return list(set(arp_entries))  # Remove duplicates

            arp_ips = await asyncio.to_thread(read_arp_table)
            logger.info(f"Found {len(arp_ips)} IPs in ARP table")
            return arp_ips

        except Exception as e:
            logger.error(f"ARP table scan failed: {e}")
            return []

    async def discover_local_network(self) -> List[dict]:
        """
        Discover devices on local network using ARP table.

        Returns:
            List of discovered devices
        """
        logger.info("Starting local network discovery via ARP table")

        # Get IPs from ARP table
        arp_ips = await self.scan_arp_table()
        if not arp_ips:
            logger.warning("No IPs found in ARP table")
            return []

        # Scan each IP for SNMP
        communities = ["public", "private", "community"]
        tasks = []
        for ip in arp_ips:
            task = self._scan_host_port(ip, 161, communities)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter successful results
        discovered_devices = []
        for result in results:
            if isinstance(result, dict) and result:
                discovered_devices.append(result)

        logger.info(f"Discovered {len(discovered_devices)} SNMP devices on local network")
        return discovered_devices

    async def close(self):
        """Close scanner and cleanup resources."""
        await self.snmp_engine.close()