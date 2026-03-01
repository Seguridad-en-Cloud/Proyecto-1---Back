"""Unit tests for QR code generation service."""
import io

import pytest
from PIL import Image

from app.services.qr_service import (
    QR_SIZE_PRESETS,
    generate_qr_png,
    generate_qr_svg,
    resolve_box_size,
)


# ── resolve_box_size ──

def test_resolve_box_size_all_presets():
    assert resolve_box_size("S") == QR_SIZE_PRESETS["S"]
    assert resolve_box_size("M") == QR_SIZE_PRESETS["M"]
    assert resolve_box_size("L") == QR_SIZE_PRESETS["L"]
    assert resolve_box_size("XL") == QR_SIZE_PRESETS["XL"]


def test_resolve_box_size_case_insensitive():
    assert resolve_box_size("s") == QR_SIZE_PRESETS["S"]
    assert resolve_box_size("xl") == QR_SIZE_PRESETS["XL"]


def test_resolve_box_size_invalid_raises():
    with pytest.raises(KeyError):
        resolve_box_size("XXL")


# ── PNG ──

def test_generate_qr_png_returns_bytes():
    result = generate_qr_png("https://example.com/m/test")
    assert isinstance(result, bytes)
    assert len(result) > 100


def test_generate_qr_png_is_valid_image():
    result = generate_qr_png("https://example.com/m/test")
    img = Image.open(io.BytesIO(result))
    assert img.format == "PNG"
    assert img.width > 0
    assert img.height > 0


def test_generate_qr_png_custom_size():
    small = generate_qr_png("https://example.com", box_size=5)
    large = generate_qr_png("https://example.com", box_size=20)
    # Larger box_size should produce more bytes
    assert len(large) > len(small)


def test_generate_qr_png_custom_border():
    result = generate_qr_png("https://example.com", border=0)
    assert isinstance(result, bytes)


def test_generate_qr_png_custom_colors():
    result = generate_qr_png(
        "https://example.com/m/test",
        fill_color="#FF0000",
        back_color="#00FF00",
    )
    img = Image.open(io.BytesIO(result))
    assert img.format == "PNG"
    assert img.width > 0


def test_generate_qr_png_named_colors():
    result = generate_qr_png(
        "https://example.com",
        fill_color="navy",
        back_color="yellow",
    )
    assert isinstance(result, bytes)
    assert len(result) > 100


# ── SVG ──

def test_generate_qr_svg_returns_bytes():
    result = generate_qr_svg("https://example.com/m/test")
    assert isinstance(result, bytes)
    assert len(result) > 100


def test_generate_qr_svg_contains_svg_tags():
    result = generate_qr_svg("https://example.com/m/test")
    text = result.decode("utf-8")
    assert "<svg" in text or "<?xml" in text


def test_generate_qr_svg_custom_params():
    result = generate_qr_svg("https://example.com", box_size=5, border=2)
    assert isinstance(result, bytes)
    assert len(result) > 0


def test_generate_qr_svg_custom_colors():
    result = generate_qr_svg(
        "https://example.com/m/test",
        fill_color="darkblue",
        back_color="#EEEEEE",
    )
    assert isinstance(result, bytes)
    assert len(result) > 100
