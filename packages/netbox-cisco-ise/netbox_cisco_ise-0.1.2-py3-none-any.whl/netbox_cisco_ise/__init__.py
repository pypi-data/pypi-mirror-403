"""
NetBox Cisco ISE Plugin

Display Cisco Identity Services Engine (ISE) endpoint and NAD information in Device detail pages.
Shows endpoint identity, profiling data, active session status, and network access device details.
"""

from netbox.plugins import PluginConfig

__version__ = "0.1.2"


class CiscoISEConfig(PluginConfig):
    """Plugin configuration for NetBox Cisco ISE integration."""

    name = "netbox_cisco_ise"
    verbose_name = "Cisco ISE"
    description = "Display Cisco ISE endpoint and NAD information in device pages"
    version = __version__
    author = "sieteunoseis"
    author_email = "jeremy.worden@gmail.com"
    base_url = "cisco-ise"
    min_version = "4.0.0"
    max_version = "4.99"

    # Required settings - plugin won't load without these
    required_settings = []

    # Default configuration values
    default_settings = {
        # ISE Connection Settings
        "ise_url": "",  # e.g., "https://ise.example.com"
        "ise_username": "",  # ERS Admin username
        "ise_password": "",  # ERS Admin password
        "timeout": 30,  # API timeout in seconds
        "cache_timeout": 60,  # Cache results for 60 seconds
        "verify_ssl": False,  # Skip SSL verification for self-signed certs
        # Device mappings - determines which devices show ISE tab and lookup method
        # Format: list of dicts with manufacturer (regex), device_type (regex, optional), lookup method
        #
        # lookup types:
        #   "endpoint" - MAC address lookup (for wireless clients, phones, badges)
        #   "nad" - Network Access Device lookup (for switches, routers, WLCs)
        #
        # Example:
        # "device_mappings": [
        #     {"manufacturer": "cisco", "lookup": "nad"},  # Cisco network devices as NADs
        #     {"manufacturer": "vocera", "lookup": "endpoint"},  # Vocera badges by MAC
        #     {"manufacturer": "cisco", "device_type": ".*phone.*", "lookup": "endpoint"},  # Cisco phones by MAC
        # ]
        "device_mappings": [
            {"manufacturer": r"cisco", "lookup": "nad"},  # Default: Cisco devices as NADs
        ],
    }


config = CiscoISEConfig
