"""Tests for ``DeviceInfo.connections`` and ``add_connection`` helper."""

from music_assistant_models.player import DeviceInfo


def test_device_info_connections_default_empty() -> None:
    """A fresh ``DeviceInfo`` has an empty connections set, not None."""
    info = DeviceInfo()
    assert info.connections == set()


def test_add_connection_normalizes_mac_with_colons() -> None:
    """Colon-separated MAC is lowercased verbatim."""
    info = DeviceInfo()
    info.add_connection("mac", "AA:BB:CC:DD:EE:FF")
    assert info.connections == {("mac", "aa:bb:cc:dd:ee:ff")}


def test_add_connection_normalizes_bluetooth_mac_with_dashes() -> None:
    """Dash-separated MAC under the ``bluetooth`` type is normalized."""
    info = DeviceInfo()
    info.add_connection("bluetooth", "AA-BB-CC-DD-EE-FF")
    assert info.connections == {("bluetooth", "aa:bb:cc:dd:ee:ff")}


def test_add_connection_normalizes_mac_without_separator() -> None:
    """No-separator MAC gets canonicalized with colons inserted."""
    info = DeviceInfo()
    info.add_connection("mac", "AABBCCDDEEFF")
    assert info.connections == {("mac", "aa:bb:cc:dd:ee:ff")}


def test_add_connection_already_canonical_mac_unchanged() -> None:
    """Already-canonical MAC round-trips through normalization."""
    info = DeviceInfo()
    info.add_connection("bluetooth", "aa:bb:cc:dd:ee:ff")
    assert info.connections == {("bluetooth", "aa:bb:cc:dd:ee:ff")}


def test_add_connection_unknown_type_stored_verbatim() -> None:
    """Provider-defined connection types pass through without filtering."""
    info = DeviceInfo()
    info.add_connection("zigbee", "00:0d:6f:00:00:00:11:22")
    info.add_connection("matter", "vendor-1234/product-5678")
    info.add_connection("custom_proto", "any-string")
    assert ("zigbee", "00:0d:6f:00:00:00:11:22") in info.connections
    assert ("matter", "vendor-1234/product-5678") in info.connections
    assert ("custom_proto", "any-string") in info.connections


def test_add_connection_non_mac_value_under_mac_type_passes_through() -> None:
    """A ``mac``-typed value that isn't 12-hex stays unchanged so we don't
    silently mangle vendor-specific identifiers."""
    info = DeviceInfo()
    info.add_connection("mac", "not-actually-a-mac")
    assert info.connections == {("mac", "not-actually-a-mac")}


def test_add_connection_empty_value_ignored() -> None:
    """Empty / None-equivalent values don't pollute the set."""
    info = DeviceInfo()
    info.add_connection("mac", "")
    assert info.connections == set()


def test_add_connection_dedupes() -> None:
    """Set semantics: same tuple added twice stays as one entry."""
    info = DeviceInfo()
    info.add_connection("mac", "AA:BB:CC:DD:EE:FF")
    info.add_connection("mac", "aa:bb:cc:dd:ee:ff")
    info.add_connection("mac", "aabbccddeeff")
    assert info.connections == {("mac", "aa:bb:cc:dd:ee:ff")}


def test_device_info_round_trip_through_dict() -> None:
    """``to_dict`` / ``from_dict`` preserves the connections set across the wire."""
    info = DeviceInfo(model="Speaker", manufacturer="Acme")
    info.add_connection("bluetooth", "AA:BB:CC:DD:EE:FF")
    info.add_connection("zigbee", "00:0d:6f:00:00:00:11:22")
    payload = info.to_dict()
    restored = DeviceInfo.from_dict(payload)
    assert restored.connections == info.connections
    assert restored.model == "Speaker"
    assert restored.manufacturer == "Acme"


def test_device_info_connections_independent_from_identifiers() -> None:
    """Connections set and identifiers dict are separate fields — no leakage."""
    info = DeviceInfo()
    info.add_connection("bluetooth", "AA:BB:CC:DD:EE:FF")
    assert info.identifiers == {}
    assert info.connections == {("bluetooth", "aa:bb:cc:dd:ee:ff")}
