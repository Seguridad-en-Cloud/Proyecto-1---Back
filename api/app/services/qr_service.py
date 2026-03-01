"""QR code generation service."""
import io
from typing import Literal

import qrcode
import qrcode.image.svg
from PIL import Image

# Named size presets as required by CU-07
QR_SIZE_PRESETS: dict[str, int] = {
    "S": 5,    # ~200×200 px
    "M": 10,   # ~400×400 px
    "L": 20,   # ~800×800 px
    "XL": 30,  # ~1200×1200 px
}

QRSizeName = Literal["S", "M", "L", "XL"]


def resolve_box_size(size: str) -> int:
    """Resolve a named size (S/M/L/XL) to a QR box_size value."""
    return QR_SIZE_PRESETS[size.upper()]


def generate_qr_png(
    url: str,
    box_size: int = 10,
    border: int = 4,
    fill_color: str = "black",
    back_color: str = "white",
) -> bytes:
    """Generate a QR code as PNG bytes.

    Args:
        url: The URL to encode in the QR.
        box_size: Size of each QR module in pixels.
        border: Border width in modules.
        fill_color: QR foreground color (hex or CSS name).
        back_color: QR background color (hex or CSS name).

    Returns:
        PNG image bytes.
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=box_size,
        border=border,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img: Image.Image = qr.make_image(fill_color=fill_color, back_color=back_color)
    output = io.BytesIO()
    img.save(output, format="PNG")
    return output.getvalue()


def generate_qr_svg(
    url: str,
    box_size: int = 10,
    border: int = 4,
    fill_color: str = "black",
    back_color: str = "white",
) -> bytes:
    """Generate a QR code as SVG bytes.

    Args:
        url: The URL to encode in the QR.
        box_size: Size of each QR module.
        border: Border width in modules.
        fill_color: QR foreground color (hex or CSS name).
        back_color: QR background color (hex or CSS name).

    Returns:
        SVG image bytes.
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=box_size,
        border=border,
    )
    qr.add_data(url)
    qr.make(fit=True)

    factory = qrcode.image.svg.SvgPathImage
    img = qr.make_image(image_factory=factory, fill_color=fill_color, back_color=back_color)
    output = io.BytesIO()
    img.save(output)
    return output.getvalue()
