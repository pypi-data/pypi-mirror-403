"""
Navigation menu items for NetBox Cisco ISE Plugin
"""

from netbox.plugins import PluginMenu, PluginMenuItem

menu = PluginMenu(
    label="Cisco ISE",
    groups=(
        (
            "Settings",
            (
                PluginMenuItem(
                    link="plugins:netbox_cisco_ise:settings",
                    link_text="Configuration",
                    permissions=["dcim.view_device"],
                ),
            ),
        ),
    ),
    icon_class="mdi mdi-shield-account",
)
