"""Info panel rendering for gemstone property display.

This module provides functions for rendering information panels
on crystal visualizations, showing properties like name, chemistry,
hardness, refractive index, etc.
"""

from collections.abc import Callable
from typing import Any

# Default property label mappings
PROPERTY_LABELS: dict[str, str] = {
    "name": "Name",
    "chemistry": "Chemistry",
    "formula": "Formula",
    "hardness": "Hardness",
    "sg": "S.G.",
    "ri": "R.I.",
    "dr": "D.R.",
    "dispersion": "Dispersion",
    "optic_sign": "Optic Sign",
    "crystal_system": "System",
    "system": "System",
    "pleochroism": "Pleochroism",
    "fluorescence": "Fluorescence",
    "lustre": "Lustre",
    "cleavage": "Cleavage",
    "fracture": "Fracture",
    "color": "Colour",
    "transparency": "Transparency",
    "habit": "Habit",
    "twinning": "Twinning",
    "treatments": "Treatments",
    "origin": "Origin",
    "species": "Species",
    "variety": "Variety",
    "phenomena": "Phenomena",
}


def get_property_label(key: str) -> str:
    """Get the display label for a property key.

    Args:
        key: Property key name

    Returns:
        Human-readable label
    """
    if key in PROPERTY_LABELS:
        return PROPERTY_LABELS[key]
    return key.replace("_", " ").title()


def format_property_value(key: str, value: Any) -> str:
    """Format a property value for display.

    Args:
        key: Property key name
        value: Property value

    Returns:
        Formatted string value
    """
    if value is None:
        return "-"

    if isinstance(value, list):
        if len(value) > 3:
            return ", ".join(str(v) for v in value[:3]) + "..."
        return ", ".join(str(v) for v in value)

    if isinstance(value, float):
        # Format floats to reasonable precision
        if abs(value) < 0.01:
            return f"{value:.4f}"
        elif abs(value) < 1:
            return f"{value:.3f}"
        else:
            return f"{value:.2f}"

    return str(value)


def render_info_panel(
    ax: Any,
    properties: dict[str, Any],
    position: str = "top-right",
    style: str = "compact",
    fontsize: int = 10,
    get_label: Callable[[str], str] | None = None,
    format_value: Callable[[str, Any], str] | None = None,
) -> None:
    """Render gemstone information panel on the visualization.

    Args:
        ax: Matplotlib axes object
        properties: Dictionary of property key -> value
        position: Panel position ('top-left', 'top-right', 'bottom-left', 'bottom-right')
        style: Panel style ('compact', 'detailed', 'minimal')
        fontsize: Base font size in points
        get_label: Optional custom function to get property labels
        format_value: Optional custom function to format property values
    """
    if not properties:
        return

    # Use custom or default formatters
    if get_label is None:
        get_label = get_property_label
    if format_value is None:
        format_value = format_property_value

    # Determine position coordinates (in axes fraction 0-1)
    positions = {
        "top-left": (0.02, 0.98, "left", "top"),
        "top-right": (0.98, 0.98, "right", "top"),
        "bottom-left": (0.02, 0.02, "left", "bottom"),
        "bottom-right": (0.98, 0.02, "right", "bottom"),
    }
    x, y, ha, va = positions.get(position, positions["top-right"])

    # Build text lines based on style
    lines = []

    if style == "minimal":
        # Just values, no labels
        for key, value in properties.items():
            lines.append(format_value(key, value))

    elif style == "detailed":
        # Full labels with grouping
        name = properties.get("name", "")
        if name:
            lines.append(name.upper())
            lines.append("-" * max(len(name), 15))

        for key, value in properties.items():
            if key == "name":
                continue
            label = get_label(key)
            formatted = format_value(key, value)
            lines.append(f"{label}: {formatted}")

    else:  # compact (default)
        # Name on first line, then key: value pairs
        name = properties.get("name", "")
        if name:
            lines.append(name)

        for key, value in properties.items():
            if key == "name":
                continue
            label = get_label(key)
            formatted = format_value(key, value)
            lines.append(f"{label}: {formatted}")

    if not lines:
        return

    # Join lines and render
    text = "\n".join(lines)

    # Create text box with semi-transparent background
    bbox_props = {
        "boxstyle": "round,pad=0.4",
        "facecolor": "white",
        "edgecolor": "#cccccc",
        "alpha": 0.9,
        "linewidth": 1,
    }

    ax.text2D(
        x,
        y,
        text,
        transform=ax.transAxes,
        fontsize=fontsize,
        fontfamily="monospace",
        ha=ha,
        va=va,
        bbox=bbox_props,
        linespacing=1.3,
    )


def create_fga_info_panel(
    mineral_data: dict[str, Any], include_keys: list | None = None
) -> dict[str, Any]:
    """Create a standardized FGA-style info panel from mineral data.

    Args:
        mineral_data: Dictionary of mineral properties
        include_keys: Optional list of keys to include (default: standard FGA set)

    Returns:
        Dictionary ready for render_info_panel
    """
    if include_keys is None:
        include_keys = [
            "name",
            "chemistry",
            "hardness",
            "sg",
            "ri",
            "dr",
            "crystal_system",
            "optic_sign",
            "pleochroism",
        ]

    result = {}
    for key in include_keys:
        if key in mineral_data and mineral_data[key] is not None:
            result[key] = mineral_data[key]

    return result
