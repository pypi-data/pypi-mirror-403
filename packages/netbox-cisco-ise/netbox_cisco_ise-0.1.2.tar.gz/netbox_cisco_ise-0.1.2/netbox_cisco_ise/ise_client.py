"""
Cisco ISE API Client

Handles authentication and API calls to Cisco Identity Services Engine (ISE).
Supports both ERS API (configuration data) and Monitoring API (session data).

ISE API Overview:
- ERS API (port 9060 or 443): Configuration data - endpoints, NADs, groups, profiles
- Monitoring API (port 443): Real-time session data

Authentication: Basic Auth (username:password) for all API calls
"""

import logging
from typing import Any, Dict, List, Optional

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class ISEClient:
    """Client for interacting with Cisco ISE ERS and Monitoring APIs."""

    def __init__(
        self,
        url: str,
        username: str,
        password: str,
        timeout: int = 30,
        verify_ssl: bool = False,
    ):
        """
        Initialize the ISE client.

        Args:
            url: Base URL for ISE (e.g., https://ise.example.com)
            username: ERS Admin username
            password: ERS Admin password
            timeout: API request timeout in seconds
            verify_ssl: Whether to verify SSL certificates
        """
        self.base_url = url.rstrip("/")
        self.auth = (username, password)
        self.timeout = timeout
        self.verify_ssl = verify_ssl

        # Standard ERS API headers
        self.ers_headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def _make_ers_request(
        self,
        endpoint: str,
        method: str = "GET",
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Make authenticated ERS API request.

        Args:
            endpoint: API endpoint path (e.g., /endpoint, /networkdevice)
            method: HTTP method (GET, POST, PUT, DELETE)
            params: Query parameters
            data: Request body data

        Returns:
            dict with response data or error
        """
        try:
            url = f"{self.base_url}/ers/config{endpoint}"
            response = requests.request(
                method=method,
                url=url,
                auth=self.auth,
                headers=self.ers_headers,
                params=params,
                json=data,
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else "Unknown"
            error_text = e.response.text[:200] if e.response else str(e)
            logger.error(f"ISE ERS HTTP error: {status_code} - {error_text}")
            return {"error": f"HTTP {status_code}: {error_text}"}
        except requests.exceptions.RequestException as e:
            logger.error(f"ISE ERS request error: {e}")
            return {"error": str(e)}

    def _make_monitoring_request(self, endpoint: str) -> Dict[str, Any]:
        """
        Make authenticated Monitoring API request.

        Args:
            endpoint: API endpoint path (e.g., /Session/MACAddress/{mac})

        Returns:
            dict with response data or error
        """
        try:
            url = f"{self.base_url}/admin/API/mnt{endpoint}"
            response = requests.get(
                url,
                auth=self.auth,
                headers=self.ers_headers,
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else "Unknown"
            # 404 is expected when no active session exists
            if status_code == 404:
                return {"error": "No active session found", "not_found": True}
            logger.error(f"ISE Monitoring HTTP error: {status_code}")
            return {"error": f"HTTP {status_code}"}
        except requests.exceptions.RequestException as e:
            logger.error(f"ISE Monitoring request error: {e}")
            return {"error": str(e)}

    # =========================================================================
    # Endpoint APIs (ERS)
    # =========================================================================

    def get_endpoint_by_mac(self, mac_address: str) -> Dict[str, Any]:
        """
        Get endpoint details by MAC address.

        Args:
            mac_address: MAC address in any common format

        Returns:
            dict with endpoint details or error
        """
        mac = self._normalize_mac(mac_address)

        # Check cache
        cache_key = f"ise_endpoint_{mac}"
        cached = cache.get(cache_key)
        if cached:
            cached["cached"] = True
            return cached

        # Query ISE ERS API with filter
        result = self._make_ers_request("/endpoint", params={"filter": f"mac.EQ.{mac}"})

        if "error" in result:
            return result

        # Parse response - ISE returns SearchResult with resources
        search_result = result.get("SearchResult", {})
        resources = search_result.get("resources", [])

        if not resources:
            return {"error": f"Endpoint not found for MAC: {mac}", "not_found": True}

        # Get full endpoint details
        endpoint_id = resources[0].get("id")
        endpoint_result = self._make_ers_request(f"/endpoint/{endpoint_id}")

        if "error" in endpoint_result:
            return endpoint_result

        endpoint = endpoint_result.get("ERSEndPoint", {})

        endpoint_info = {
            "id": endpoint.get("id"),
            "mac_address": endpoint.get("mac"),
            "profile_name": endpoint.get("profileName"),
            "profile_id": endpoint.get("profileId"),
            "group_name": endpoint.get("groupName"),
            "group_id": endpoint.get("groupId"),
            "static_group_assignment": endpoint.get("staticGroupAssignment", False),
            "static_profile_assignment": endpoint.get("staticProfileAssignment", False),
            "portal_user": endpoint.get("portalUser"),
            "identity_store": endpoint.get("identityStore"),
            "identity_store_id": endpoint.get("identityStoreId"),
            "custom_attributes": endpoint.get("customAttributes", {}),
            "description": endpoint.get("description"),
            "cached": False,
        }

        # Cache result
        cache_timeout = self._get_cache_timeout()
        cache.set(cache_key, endpoint_info, cache_timeout)

        return endpoint_info

    def get_active_session_by_mac(self, mac_address: str) -> Dict[str, Any]:
        """
        Get active session for endpoint by MAC address.

        Args:
            mac_address: MAC address in any common format

        Returns:
            dict with session details or error/not connected status
        """
        mac = self._normalize_mac(mac_address)

        cache_key = f"ise_session_{mac}"
        cached = cache.get(cache_key)
        if cached:
            cached["cached"] = True
            return cached

        result = self._make_monitoring_request(f"/Session/MACAddress/{mac}")

        if "error" in result:
            if result.get("not_found"):
                return {"connected": False, "error": "No active session found"}
            return result

        # Handle different response structures
        session = result.get("activeSession") or result.get("session", {})

        if not session:
            return {"connected": False, "error": "No active session found"}

        session_info = {
            "connected": True,
            "session_id": session.get("session_id") or session.get("acs_session_id"),
            "user_name": session.get("user_name"),
            "calling_station_id": session.get("calling_station_id"),
            "nas_ip_address": session.get("nas_ip_address"),
            "nas_port_id": session.get("nas_port_id"),
            "nas_port_type": session.get("nas_port_type"),
            "framed_ip_address": session.get("framed_ip_address"),
            "framed_ipv6_address": session.get("framed_ipv6_address"),
            "audit_session_id": session.get("audit_session_id"),
            "acct_session_id": session.get("acct_session_id"),
            "acct_session_time": session.get("acct_session_time"),
            "authorization_profile": session.get("selected_authorization_profile"),
            "posture_status": session.get("posture_status"),
            "security_group": session.get("security_group"),
            "vlan": session.get("vlan"),
            "ssid": session.get("ssid"),
            "auth_method": session.get("authentication_method"),
            "network_device_name": session.get("network_device_name"),
            "acs_server": session.get("acs_server"),
            "cached": False,
        }

        cache_timeout = self._get_cache_timeout()
        cache.set(cache_key, session_info, cache_timeout)

        return session_info

    # =========================================================================
    # Network Device (NAD) APIs (ERS)
    # =========================================================================

    def get_network_device_by_ip(self, ip_address: str) -> Dict[str, Any]:
        """
        Get NAD details by IP address.

        Args:
            ip_address: Management IP address

        Returns:
            dict with NAD details or error
        """
        cache_key = f"ise_nad_ip_{ip_address}"
        cached = cache.get(cache_key)
        if cached:
            cached["cached"] = True
            return cached

        result = self._make_ers_request("/networkdevice", params={"filter": f"ipaddress.EQ.{ip_address}"})

        return self._process_nad_result(result, cache_key)

    def get_network_device_by_name(self, name: str) -> Dict[str, Any]:
        """
        Get NAD details by device name.

        Args:
            name: Device name (supports partial match)

        Returns:
            dict with NAD details or error
        """
        cache_key = f"ise_nad_name_{name}"
        cached = cache.get(cache_key)
        if cached:
            cached["cached"] = True
            return cached

        result = self._make_ers_request("/networkdevice", params={"filter": f"name.CONTAINS.{name}"})

        return self._process_nad_result(result, cache_key)

    def _process_nad_result(self, result: Dict, cache_key: str) -> Dict[str, Any]:
        """Process NAD search result and fetch full details."""
        if "error" in result:
            return result

        search_result = result.get("SearchResult", {})
        resources = search_result.get("resources", [])

        if not resources:
            return {"error": "Network device not found in ISE", "not_found": True, "is_nad": False}

        # Get full NAD details
        nad_id = resources[0].get("id")
        nad_result = self._make_ers_request(f"/networkdevice/{nad_id}")

        if "error" in nad_result:
            return nad_result

        nad = nad_result.get("NetworkDevice", {})

        # Parse network device groups
        groups = nad.get("NetworkDeviceGroupList", [])
        parsed_groups = self._parse_device_groups(groups)

        # Parse IP addresses
        ip_list = nad.get("NetworkDeviceIPList", [])
        ip_addresses = [ip.get("ipaddress") for ip in ip_list if ip.get("ipaddress")]

        # Parse authentication settings
        auth_settings = nad.get("authenticationSettings", {})
        tacacs_settings = nad.get("tacacsSettings", {})
        snmp_settings = nad.get("snmpsettings", {})
        trustsec_settings = nad.get("trustsecsettings", {})

        nad_info = {
            "is_nad": True,
            "id": nad.get("id"),
            "name": nad.get("name"),
            "description": nad.get("description"),
            "profile_name": nad.get("profileName"),
            "model_name": nad.get("modelName"),
            "software_version": nad.get("softwareVersion"),
            "ip_addresses": ip_addresses,
            "groups": parsed_groups,
            "authentication_settings": {
                "radius_enabled": bool(auth_settings.get("radiusSharedSecret")),
                "enable_key_wrap": auth_settings.get("enableKeyWrap", False),
                "dtls_required": auth_settings.get("dtlsRequired", False),
            },
            "tacacs_settings": {
                "enabled": bool(tacacs_settings.get("sharedSecret")),
                "connect_mode_options": tacacs_settings.get("connectModeOptions"),
            },
            "snmp_settings": {
                "version": snmp_settings.get("snmpVersion"),
                "ro_community": bool(snmp_settings.get("roCommunity")),
                "polling_interval": snmp_settings.get("pollingInterval"),
            },
            "trustsec_enabled": bool(trustsec_settings.get("deviceAuthenticationSettings", {}).get("sgaDeviceId")),
            "coA_port": nad.get("coaPort"),
            "cached": False,
        }

        cache_timeout = self._get_cache_timeout()
        cache.set(cache_key, nad_info, cache_timeout)

        return nad_info

    def _parse_device_groups(self, groups: List[str]) -> Dict[str, str]:
        """
        Parse ISE device group strings into categorized dict.

        ISE group format: "Category#All Category#Value" or "Location#All Locations#Building-A"

        Args:
            groups: List of group strings from ISE

        Returns:
            dict mapping category to value
        """
        parsed = {}
        for group in groups:
            parts = group.split("#")
            if len(parts) >= 2:
                category = parts[0]
                value = parts[-1]  # Last part is the actual value
                parsed[category] = value
        return parsed

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def _normalize_mac(self, mac: str) -> str:
        """
        Normalize MAC address to XX:XX:XX:XX:XX:XX format (ISE standard).

        Args:
            mac: MAC address in any common format

        Returns:
            MAC address in XX:XX:XX:XX:XX:XX uppercase format
        """
        mac_clean = mac.replace(":", "").replace("-", "").replace(".", "").lower()
        if len(mac_clean) == 12:
            return ":".join(mac_clean[i : i + 2] for i in range(0, 12, 2)).upper()
        return mac.upper()

    def _get_cache_timeout(self) -> int:
        """Get cache timeout from plugin config."""
        config = settings.PLUGINS_CONFIG.get("netbox_cisco_ise", {})
        return config.get("cache_timeout", 60)

    def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to ISE by fetching network device count.

        Returns:
            dict with success status and message
        """
        result = self._make_ers_request("/networkdevice", params={"size": 1})

        if "error" in result:
            return {"success": False, "error": result["error"]}

        total = result.get("SearchResult", {}).get("total", 0)
        return {
            "success": True,
            "message": f"Connected successfully. {total} network device(s) in ISE.",
            "nad_count": total,
        }


def get_client() -> Optional[ISEClient]:
    """
    Get configured ISE client instance from plugin settings.

    Returns:
        ISEClient instance or None if not configured
    """
    config = settings.PLUGINS_CONFIG.get("netbox_cisco_ise", {})

    url = config.get("ise_url", "")
    username = config.get("ise_username", "")
    password = config.get("ise_password", "")

    if not url or not username or not password:
        return None

    return ISEClient(
        url=url,
        username=username,
        password=password,
        timeout=config.get("timeout", 30),
        verify_ssl=config.get("verify_ssl", False),
    )
