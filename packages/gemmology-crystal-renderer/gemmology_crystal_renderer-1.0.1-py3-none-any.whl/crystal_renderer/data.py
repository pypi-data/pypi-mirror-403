"""Crystal rendering constants and colour schemes.

This module contains all shared constants used across the crystal visualization
modules, including colour schemes for crystallographic axes, elements, habits,
and crystal system parameters.
"""

# Colour scheme for crystallographic axes
AXIS_COLOURS: dict[str, str] = {
    "a": "#E53935",  # Red
    "b": "#43A047",  # Green
    "c": "#1E88E5",  # Blue
}

# Element colours (subset of Jmol colours)
ELEMENT_COLOURS: dict[str, str] = {
    "C": "#909090",  # Carbon - grey
    "O": "#FF0D0D",  # Oxygen - red
    "Al": "#BFA6A6",  # Aluminium - pinkish grey
    "Si": "#F0C8A0",  # Silicon - beige
    "Mg": "#8AFF00",  # Magnesium - bright green
    "Be": "#C2FF00",  # Beryllium - yellow-green
    "Fe": "#E06633",  # Iron - orange
    "Cr": "#8A99C7",  # Chromium - blue-grey
    "Ti": "#BFC2C7",  # Titanium - silver
    "Zr": "#94E0E0",  # Zirconium - cyan
    "Li": "#CC80FF",  # Lithium - purple
    "F": "#90E050",  # Fluorine - green
    "Ca": "#3DFF00",  # Calcium - green
    "Mn": "#9C7AC7",  # Manganese - purple
    "Cu": "#C88033",  # Copper - copper colour
    "P": "#FF8000",  # Phosphorus - orange
    "B": "#FFB5B5",  # Boron - pink
    "Na": "#AB5CF2",  # Sodium - violet
    "S": "#FFFF30",  # Sulphur - yellow
}

# Crystal system unit cells (for generic crystal system visualization)
CRYSTAL_SYSTEMS: dict[str, dict[str, float]] = {
    "cubic": {"a": 4.0, "b": 4.0, "c": 4.0, "alpha": 90, "beta": 90, "gamma": 90},
    "tetragonal": {"a": 4.0, "b": 4.0, "c": 6.0, "alpha": 90, "beta": 90, "gamma": 90},
    "orthorhombic": {"a": 4.0, "b": 5.0, "c": 6.0, "alpha": 90, "beta": 90, "gamma": 90},
    "hexagonal": {"a": 4.0, "b": 4.0, "c": 6.0, "alpha": 90, "beta": 90, "gamma": 120},
    "trigonal": {"a": 4.0, "b": 4.0, "c": 4.0, "alpha": 80, "beta": 80, "gamma": 80},
    "monoclinic": {"a": 4.0, "b": 5.0, "c": 6.0, "alpha": 90, "beta": 110, "gamma": 90},
    "triclinic": {"a": 4.0, "b": 5.0, "c": 6.0, "alpha": 80, "beta": 85, "gamma": 95},
}

# Habit face colours by crystal system
HABIT_COLOURS: dict[str, dict[str, str]] = {
    "cubic": {"face": "#81D4FA", "edge": "#0277BD"},  # Light blue
    "tetragonal": {"face": "#CE93D8", "edge": "#7B1FA2"},  # Purple
    "hexagonal": {"face": "#A5D6A7", "edge": "#388E3C"},  # Green
    "trigonal": {"face": "#FFCC80", "edge": "#EF6C00"},  # Orange
    "orthorhombic": {"face": "#EF9A9A", "edge": "#C62828"},  # Red
    "monoclinic": {"face": "#B0BEC5", "edge": "#455A64"},  # Blue-grey
    "triclinic": {"face": "#FFAB91", "edge": "#BF360C"},  # Deep orange
}

# Colors for different crystal forms (used with color_by_form)
FORM_COLORS: list[dict[str, str]] = [
    {"face": "#81D4FA", "edge": "#0277BD"},  # Form 0 - Light blue
    {"face": "#EF9A9A", "edge": "#C62828"},  # Form 1 - Light red
    {"face": "#A5D6A7", "edge": "#388E3C"},  # Form 2 - Light green
    {"face": "#CE93D8", "edge": "#7B1FA2"},  # Form 3 - Light purple
    {"face": "#FFCC80", "edge": "#EF6C00"},  # Form 4 - Light orange
    {"face": "#80DEEA", "edge": "#00838F"},  # Form 5 - Cyan
    {"face": "#F48FB1", "edge": "#AD1457"},  # Form 6 - Pink
    {"face": "#C5E1A5", "edge": "#558B2F"},  # Form 7 - Lime green
]

# Twin colour scheme (alternating colours for twin components)
TWIN_COLOURS: list[dict[str, str]] = [
    {"face": "#81D4FA", "edge": "#0277BD"},  # Light blue
    {"face": "#FFCC80", "edge": "#EF6C00"},  # Orange
    {"face": "#A5D6A7", "edge": "#388E3C"},  # Green
]

# Cleavage plane colour
CLEAVAGE_COLOUR: dict[str, str] = {"face": "#FF5722", "edge": "#BF360C"}
