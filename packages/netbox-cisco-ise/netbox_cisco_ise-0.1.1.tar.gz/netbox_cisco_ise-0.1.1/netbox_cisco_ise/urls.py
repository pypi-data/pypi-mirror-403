"""
URL routing for NetBox Cisco ISE Plugin
"""

from django.urls import path

from .views import ISESettingsView, TestConnectionView

urlpatterns = [
    path("settings/", ISESettingsView.as_view(), name="settings"),
    path("test-connection/", TestConnectionView.as_view(), name="test_connection"),
]
