"""
Views for NetBox Cisco ISE Plugin

Registers custom tabs on Device detail views to show ISE endpoint/NAD info.
Provides settings configuration UI.
"""

import re

from dcim.models import Device
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
from netbox.views import generic
from utilities.views import ViewTab, register_model_view

from .ise_client import get_client


def is_valid_mac(value):
    """Check if a value looks like a MAC address."""
    if not value:
        return False
    cleaned = re.sub(r"[:\-\.]", "", value.lower())
    return bool(re.match(r"^[0-9a-f]{12}$", cleaned))


def get_device_mac(device):
    """Get the first valid MAC address from device interfaces."""
    for iface in device.interfaces.all():
        if iface.mac_address and is_valid_mac(str(iface.mac_address)):
            return str(iface.mac_address)
    return None


def get_device_lookup_method(device):
    """
    Determine the lookup method for a device based on configured mappings.

    Returns:
        tuple: (lookup_method, has_required_data)
        - lookup_method: "endpoint", "nad", or None if no mapping matches
        - has_required_data: True if device has the data needed for lookup
    """
    config = settings.PLUGINS_CONFIG.get("netbox_cisco_ise", {})
    mappings = config.get("device_mappings", [])

    if not device.device_type:
        return None, False

    # Get device info for matching
    manufacturer = device.device_type.manufacturer
    manufacturer_slug = manufacturer.slug.lower() if manufacturer and manufacturer.slug else ""
    manufacturer_name = manufacturer.name.lower() if manufacturer and manufacturer.name else ""
    device_type_slug = device.device_type.slug.lower() if device.device_type.slug else ""
    device_type_model = device.device_type.model.lower() if device.device_type.model else ""

    # Check each mapping
    for mapping in mappings:
        manufacturer_pattern = mapping.get("manufacturer", "").lower()
        device_type_pattern = mapping.get("device_type", "").lower()
        lookup = mapping.get("lookup", "nad")

        # Check manufacturer match (against both slug and name)
        manufacturer_match = False
        if manufacturer_pattern:
            try:
                if re.search(manufacturer_pattern, manufacturer_slug, re.IGNORECASE) or re.search(
                    manufacturer_pattern, manufacturer_name, re.IGNORECASE
                ):
                    manufacturer_match = True
            except re.error:
                if manufacturer_pattern in manufacturer_slug or manufacturer_pattern in manufacturer_name:
                    manufacturer_match = True

        if not manufacturer_match:
            continue

        # Check device_type match if specified
        if device_type_pattern:
            device_type_match = False
            try:
                if re.search(device_type_pattern, device_type_slug, re.IGNORECASE) or re.search(
                    device_type_pattern, device_type_model, re.IGNORECASE
                ):
                    device_type_match = True
            except re.error:
                if device_type_pattern in device_type_slug or device_type_pattern in device_type_model:
                    device_type_match = True

            if not device_type_match:
                continue

        # Mapping matches! Return lookup type and check if device has required data
        if lookup == "endpoint":
            # Endpoint lookup - requires MAC address
            mac = get_device_mac(device)
            return "endpoint", mac is not None
        else:
            # NAD lookup - requires hostname or IP
            has_hostname = bool(device.name)
            has_ip = device.primary_ip4 is not None or device.primary_ip6 is not None
            return "nad", (has_hostname or has_ip)

    return None, False


def should_show_ise_tab(device):
    """
    Determine if the ISE tab should be visible for this device.

    Shows tab if device matches any configured device_mapping and has
    the required data for the lookup method.
    """
    lookup_method, has_data = get_device_lookup_method(device)
    return lookup_method is not None and has_data


@register_model_view(Device, name="cisco_ise", path="cisco-ise")
class DeviceISEView(generic.ObjectView):
    """Display Cisco ISE endpoint/NAD details for a Device."""

    queryset = Device.objects.all()
    template_name = "netbox_cisco_ise/endpoint_tab.html"

    tab = ViewTab(
        label="Cisco ISE",
        weight=9001,
        permission="dcim.view_device",
        hide_if_empty=False,
        visible=should_show_ise_tab,
    )

    def get(self, request, pk):
        """Handle GET request for the ISE tab."""
        device = Device.objects.select_related("device_type__manufacturer").prefetch_related("interfaces").get(pk=pk)

        client = get_client()
        config = settings.PLUGINS_CONFIG.get("netbox_cisco_ise", {})

        ise_data = {}
        session_data = {}
        error = None

        if not client:
            error = "Cisco ISE not configured. Configure the plugin in NetBox settings."
        else:
            lookup_method, has_data = get_device_lookup_method(device)

            if lookup_method == "endpoint":
                # Endpoint lookup by MAC address
                mac_address = get_device_mac(device)
                if mac_address:
                    ise_data = client.get_endpoint_by_mac(mac_address)
                    if "error" not in ise_data:
                        # Also get session data for connected endpoints
                        session_data = client.get_active_session_by_mac(mac_address)
                        if "error" in session_data and session_data.get("connected") is False:
                            # Not connected is fine, just no active session
                            pass
                    else:
                        error = ise_data.get("error")
                        ise_data = {}
                else:
                    error = "No MAC address found on device interfaces."

            elif lookup_method == "nad":
                # NAD lookup - try IP first, then hostname
                management_ip = None
                if device.primary_ip4:
                    management_ip = str(device.primary_ip4.address.ip)
                elif device.primary_ip6:
                    management_ip = str(device.primary_ip6.address.ip)

                if management_ip:
                    ise_data = client.get_network_device_by_ip(management_ip)

                # If IP lookup failed or no IP, try hostname
                if ("error" in ise_data or not ise_data) and device.name:
                    ise_data = client.get_network_device_by_name(device.name)

                if "error" in ise_data:
                    error = ise_data.get("error")
                    ise_data = {}
            else:
                error = "Device doesn't match any configured device_mappings."

        # Get ISE URL for external links
        ise_url = config.get("ise_url", "").rstrip("/")

        # Choose template based on lookup type
        if ise_data.get("is_nad"):
            template = "netbox_cisco_ise/nad_tab.html"
        else:
            template = self.template_name

        return render(
            request,
            template,
            {
                "object": device,
                "tab": self.tab,
                "ise_data": ise_data,
                "session_data": session_data,
                "error": error,
                "ise_url": ise_url,
            },
        )


class ISESettingsView(View):
    """View for displaying ISE plugin settings."""

    template_name = "netbox_cisco_ise/settings.html"

    def get(self, request):
        """Display current configuration."""
        config = settings.PLUGINS_CONFIG.get("netbox_cisco_ise", {})

        # Mask password for display
        display_config = config.copy()
        if display_config.get("ise_password"):
            display_config["ise_password"] = "********"

        return render(
            request,
            self.template_name,
            {
                "config": display_config,
            },
        )


class TestConnectionView(View):
    """Test connection to ISE API."""

    def post(self, request):
        """Test ISE connection and return result."""
        client = get_client()
        if not client:
            return JsonResponse(
                {"success": False, "error": "ISE not configured"},
                status=400,
            )

        result = client.test_connection()
        if not result.get("success"):
            return JsonResponse(result, status=400)

        return JsonResponse(result)
