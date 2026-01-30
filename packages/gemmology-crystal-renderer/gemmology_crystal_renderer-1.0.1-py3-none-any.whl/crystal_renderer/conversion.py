"""Crystal format conversion utilities.

This module handles conversion between SVG and raster formats (PNG, JPG, BMP),
as well as 3D format exports (STL, glTF, GEMCAD).
"""

import io
import os
import tempfile
from collections.abc import Callable
from pathlib import Path

# Check for optional dependencies
try:
    import cairosvg

    CAIROSVG_AVAILABLE = True
except ImportError:
    CAIROSVG_AVAILABLE = False

try:
    from PIL import Image

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


def convert_svg_to_raster(
    svg_path: str | Path,
    output_path: str | Path,
    output_format: str = "png",
    scale: float = 2.0,
    quality: int = 95,
) -> Path:
    """Convert SVG to raster format (PNG, JPG, BMP).

    Args:
        svg_path: Path to input SVG file
        output_path: Path for output raster file
        output_format: 'png', 'jpg', 'jpeg', or 'bmp'
        scale: Scale factor for higher resolution (default 2x)
        quality: JPEG quality (1-100, default 95)

    Returns:
        Path to output file

    Raises:
        ImportError: If required libraries not available
        ValueError: If format not supported
    """
    output_format = output_format.lower()
    if output_format == "jpeg":
        output_format = "jpg"

    if output_format not in ("png", "jpg", "bmp"):
        raise ValueError(f"Unsupported format: {output_format}. Use png, jpg, or bmp.")

    if not CAIROSVG_AVAILABLE:
        raise ImportError("cairosvg not available. Install with: pip install cairosvg")

    svg_path = Path(svg_path)
    output_path = Path(output_path)

    # Convert SVG to PNG using cairosvg
    png_data = cairosvg.svg2png(url=str(svg_path), scale=scale)

    if output_format == "png":
        # Direct PNG output
        with open(output_path, "wb") as f:
            f.write(png_data)
    else:
        # Convert PNG to JPG or BMP using PIL
        if not PIL_AVAILABLE:
            raise ImportError("PIL not available. Install with: pip install Pillow")

        img = Image.open(io.BytesIO(png_data))

        # Convert RGBA to RGB for formats that don't support alpha
        if img.mode == "RGBA":
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])
            img = background

        if output_format == "jpg":
            img.save(output_path, "JPEG", quality=quality)
        elif output_format == "bmp":
            img.save(output_path, "BMP")

    return output_path


def generate_with_format(
    generator_func: Callable,
    output_path: str | Path,
    output_format: str = "svg",
    scale: float = 2.0,
    quality: int = 95,
    **kwargs,
) -> Path:
    """Generate crystal visualization in specified format.

    Args:
        generator_func: Function that generates SVG
        output_path: Output file path
        output_format: 'svg', 'png', 'jpg', or 'bmp'
        scale: Scale factor for raster output
        quality: JPEG quality
        **kwargs: Additional arguments for generator_func

    Returns:
        Path to output file

    Raises:
        ValueError: If format not supported
    """
    output_format = output_format.lower()
    if output_format == "jpeg":
        output_format = "jpg"

    output_path = Path(output_path)

    # For SVG, just call the generator directly
    if output_format == "svg":
        result = generator_func(output_path=str(output_path), **kwargs)
        return Path(result) if isinstance(result, str) else output_path

    # For raster formats, generate SVG to temp file then convert
    if output_format in ("png", "jpg", "bmp"):
        with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as tmp:
            tmp_svg = tmp.name

        try:
            generator_func(output_path=tmp_svg, **kwargs)

            # Adjust output path extension
            if output_path.suffix.lower() == ".svg":
                output_path = output_path.with_suffix("." + output_format)

            convert_svg_to_raster(tmp_svg, output_path, output_format, scale, quality)
            return output_path
        finally:
            if os.path.exists(tmp_svg):
                os.remove(tmp_svg)

    raise ValueError(f"Unsupported format: {output_format}")


def check_dependencies() -> dict:
    """Check availability of optional conversion dependencies.

    Returns:
        Dictionary with dependency status
    """
    return {
        "cairosvg": CAIROSVG_AVAILABLE,
        "pillow": PIL_AVAILABLE,
    }
