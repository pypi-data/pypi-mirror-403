# NetBox Cisco ISE Plugin

<img src="https://raw.githubusercontent.com/sieteunoseis/netbox-cisco-ise/main/docs/icon.png" alt="NetBox Cisco ISE Plugin" width="100" align="right">

A NetBox plugin that integrates Cisco Identity Services Engine (ISE) with NetBox, displaying endpoint details, network device (NAD) information, and active session data.

![NetBox Version](https://img.shields.io/badge/NetBox-4.0+-blue)
![Python Version](https://img.shields.io/badge/Python-3.10+-green)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![CI](https://github.com/sieteunoseis/netbox-cisco-ise/actions/workflows/ci.yml/badge.svg)](https://github.com/sieteunoseis/netbox-cisco-ise/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/netbox-cisco-ise)](https://pypi.org/project/netbox-cisco-ise/)

## Features

### Endpoint Integration
- **Endpoint Details Tab**: Adds a "Cisco ISE" tab to Device detail pages for endpoints
- **MAC Address Lookup**: Automatic lookup using device interface MAC addresses
- **Endpoint Profile**: Shows profiled device type and identity group
- **Session Status**: Displays active/inactive connection status

### Network Access Device (NAD) Integration
- **NAD Details Tab**: Shows ISE registration status for network devices
- **Authentication Settings**: Displays RADIUS, TACACS+, and SNMP configuration
- **TrustSec Status**: Shows device TrustSec enrollment
- **Device Groups**: Lists assigned network device groups

### Active Session Data
- **Real-time Session**: Shows active 802.1X/MAB session details
- **Connection Info**: NAS IP, port ID, VLAN assignment
- **Authorization**: Selected authorization profile and SGT
- **Posture Status**: Endpoint compliance posture state

### General Features
- **Configurable Device Mappings**: Control which devices show the tab and lookup method
- **API Caching**: Reduces load on ISE with configurable cache timeout
- **Settings Page**: View configuration and test ISE connection

## Requirements

- NetBox 4.0 or higher
- Cisco ISE 2.x or higher with ERS API enabled
- Python 3.10+

## Installation

### From PyPI (recommended)

```bash
pip install netbox-cisco-ise
```

### From Source

```bash
git clone https://github.com/sieteunoseis/netbox-cisco-ise.git
cd netbox-cisco-ise
pip install -e .
```

### Docker Installation

Add to your NetBox Docker requirements file:

```bash
# requirements-extra.txt
netbox-cisco-ise
```

Or for development:

```bash
# In docker-compose.override.yml, mount the plugin:
volumes:
  - /path/to/netbox-cisco-ise:/opt/netbox/netbox/netbox_cisco_ise
```

## Configuration

Add the plugin to your NetBox configuration:

```python
# configuration.py

PLUGINS = [
    'netbox_cisco_ise',
]

PLUGINS_CONFIG = {
    'netbox_cisco_ise': {
        # Required: ISE URL (ERS API)
        'ise_url': 'https://ise.example.com',

        # Required: ERS Admin credentials
        'ise_username': 'ersadmin',
        'ise_password': 'your-password',

        # Optional settings
        'timeout': 30,           # API timeout in seconds (default: 30)
        'cache_timeout': 60,     # Cache duration in seconds (default: 60)
        'verify_ssl': False,     # Verify SSL certificates (default: False)

        # Device mappings (REQUIRED) - Controls which devices show the Cisco ISE tab
        # Each mapping specifies:
        #   - manufacturer: Regex pattern to match device manufacturer (slug or name)
        #   - device_type: Optional regex pattern to match device type (slug or model)
        #   - lookup: How to find the device in ISE:
        #       "nad" - Network Access Device lookup by IP/hostname (for switches, routers, WLCs)
        #       "endpoint" - Endpoint lookup by MAC address (for wireless clients, badges)
        'device_mappings': [
            # All Cisco devices - lookup as NADs
            {'manufacturer': 'cisco', 'lookup': 'nad'},

            # Vocera badges - lookup by MAC address as endpoints
            {'manufacturer': 'vocera', 'lookup': 'endpoint'},

            # Example: Specific device type only
            # {'manufacturer': 'aruba', 'device_type': 'badge', 'lookup': 'endpoint'},
        ],
    }
}
```

### ISE ERS API Setup

1. Enable ERS API in ISE: **Administration > System > Settings > ERS Settings**
2. Create an ERS Admin user or use existing admin credentials
3. Ensure the user has "ERS Admin" or "ERS Operator" privileges

### Required ISE Permissions

| Permission | Used For |
|------------|----------|
| ERS Read | Endpoint and NAD queries |
| Monitoring API | Active session lookups |

## Usage

Once installed and configured:

1. Navigate to any Device in NetBox that matches your device_mappings
2. Click the **Cisco ISE** tab
3. View real-time endpoint or NAD details from ISE

### Lookup Methods

| Lookup | Data Source | Used For |
|--------|-------------|----------|
| `nad` | IP address or hostname | Switches, routers, WLCs, APs |
| `endpoint` | Interface MAC address | Wireless clients, badges, phones |

### What's Displayed

#### For Endpoints (lookup: endpoint)

| Field | Description |
|-------|-------------|
| MAC Address | Endpoint MAC from ISE |
| Profile | Profiled endpoint type |
| Identity Group | Assigned identity group |
| Session Status | Connected/Disconnected |
| NAS IP | Authenticator IP address |
| Port | Switch port or AP name |
| VLAN | Assigned VLAN |
| Authorization | Applied authorization profile |

#### For NADs (lookup: nad)

| Field | Description |
|-------|-------------|
| Name | Device name in ISE |
| IP Addresses | Registered management IPs |
| Profile | NAD profile name |
| Device Groups | Location, type, IPSEC groups |
| RADIUS | Shared secret configured |
| TACACS+ | TACACS+ settings |
| TrustSec | SGT enrollment status |

## Troubleshooting

### Endpoint not found

- Verify the device has an interface with a MAC address
- Check that the MAC format matches ISE (XX:XX:XX:XX:XX:XX)
- Confirm the endpoint exists in ISE endpoint database

### NAD not found

- Verify the device has a primary IP or hostname in NetBox
- Check that the device is registered as a NAD in ISE
- Try both IP and hostname lookups

### Connection errors

- Verify `ise_url` is accessible from NetBox
- Confirm ERS API is enabled on ISE
- For self-signed certificates, set `verify_ssl: False`

### Authentication errors

- Verify the ERS Admin credentials
- Check user has ERS Admin or ERS Operator role

## Development

### Setup

```bash
git clone https://github.com/sieteunoseis/netbox-cisco-ise.git
cd netbox-cisco-ise
pip install -e ".[dev]"
```

### Code Style

```bash
black netbox_cisco_ise/
isort netbox_cisco_ise/
flake8 netbox_cisco_ise/
```

## API Reference

This plugin uses two ISE APIs:

- **ERS API** (`/ers/config/*`): Configuration data - endpoints, NADs, profiles
- **Monitoring API** (`/admin/API/mnt/*`): Real-time session data

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for release history.

## License

Apache License 2.0 - See [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## Related Projects

- [netbox-catalyst-center](https://github.com/sieteunoseis/netbox-catalyst-center) - Catalyst Center integration for NetBox
- [netbox-graylog](https://github.com/sieteunoseis/netbox-graylog) - Display Graylog logs in NetBox
