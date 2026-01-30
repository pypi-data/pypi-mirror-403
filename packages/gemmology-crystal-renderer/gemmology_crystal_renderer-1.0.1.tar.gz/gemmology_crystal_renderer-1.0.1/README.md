# Crystal Renderer

SVG and 3D visualization for crystal geometries. Renders crystal structures from CDL notation with export to multiple formats including SVG, STL, and glTF.

Part of the [Gemmology Project](https://gemmology.dev).

## Installation

```bash
pip install crystal-renderer
```

For raster image export (PNG, JPG):
```bash
pip install crystal-renderer[raster]
```

## Quick Start

```python
from crystal_renderer import generate_cdl_svg

# Generate SVG from CDL notation
generate_cdl_svg("cubic[m3m]:{111}@1.0 + {100}@1.3", "crystal.svg")

# Export to 3D formats
from crystal_geometry import create_octahedron
from crystal_renderer import export_stl, export_gltf

geom = create_octahedron()
export_stl(geom.vertices, geom.faces, "octahedron.stl")
export_gltf(geom.vertices, geom.faces, "octahedron.gltf")
```

## Features

- **CDL Visualization**: Generate SVG images from Crystal Description Language notation
- **Multi-Format Export**: SVG, PNG, JPG, STL, glTF
- **Customizable Rendering**: Face colors, axes, grid, labels
- **Info Panels**: FGA-style property panels on visualizations
- **3D Projection**: Configurable elevation and azimuth angles
- **Color Schemes**: System-based and form-based coloring

## API Reference

### High-Level Visualization

```python
from crystal_renderer import generate_cdl_svg, generate_geometry_svg

# From CDL string
generate_cdl_svg(
    cdl_string="cubic[m3m]:{111}@1.0",
    output_path="crystal.svg",
    show_axes=True,
    elev=30,
    azim=-45,
    color_by_form=False,
    show_grid=True,
    face_labels=False
)

# From raw geometry
generate_geometry_svg(
    vertices=geom.vertices,
    faces=geom.faces,
    output_path="geometry.svg",
    face_color='#81D4FA',
    edge_color='#0277BD'
)
```

### 3D Export

```python
from crystal_renderer import export_stl, export_gltf

# STL for 3D printing
export_stl(vertices, faces, "model.stl", binary=True)

# glTF for web/AR
export_gltf(
    vertices, faces, "model.gltf",
    color=(0.5, 0.7, 0.9, 0.8),  # RGBA
    name="crystal"
)
```

### Format Conversion

```python
from crystal_renderer import convert_svg_to_raster, generate_with_format

# Convert existing SVG to PNG
convert_svg_to_raster("input.svg", "output.png", scale=2.0)

# Generate directly to raster format
generate_with_format(
    generator_func=generate_cdl_svg,
    output_path="crystal.png",
    output_format="png",
    cdl_string="cubic[m3m]:{111}"
)
```

### Info Panels

```python
from crystal_renderer import render_info_panel, create_fga_info_panel

# On a matplotlib axes
properties = {
    'name': 'Ruby',
    'chemistry': 'Al2O3',
    'hardness': '9',
    'ri': '1.762-1.770'
}
render_info_panel(ax, properties, position='top-right', style='compact')

# Create FGA-style panel from mineral data
fga_props = create_fga_info_panel(mineral_data)
```

### Color Constants

```python
from crystal_renderer import (
    AXIS_COLOURS,      # a, b, c axis colors
    ELEMENT_COLOURS,   # Per-element colors
    HABIT_COLOURS,     # Per-crystal-system colors
    FORM_COLORS,       # Colors for multi-form rendering
)

# Get element color
from crystal_renderer import get_element_colour
color = get_element_colour('Si')  # '#F0C8A0'
```

### Projection Utilities

```python
from crystal_renderer import (
    calculate_view_direction,
    calculate_axis_origin,
    calculate_vertex_visibility,
    is_face_visible,
)

# Calculate which vertices are front-facing
visibility = calculate_vertex_visibility(vertices, faces, elev=30, azim=-45)
```

## Output Formats

| Format | Extension | Description |
|--------|-----------|-------------|
| SVG | `.svg` | Vector graphics, scalable |
| PNG | `.png` | Raster with transparency |
| JPG | `.jpg` | Compressed raster |
| STL | `.stl` | 3D printing format |
| glTF | `.gltf` | Web/AR 3D format |

## Requirements

- Python >= 3.10
- numpy >= 1.20.0
- matplotlib >= 3.5.0
- cdl-parser >= 1.0.0
- crystal-geometry >= 1.0.0

### Optional

- `cairosvg` - SVG to raster conversion
- `Pillow` - Image processing
- `ase` - Atomic structure visualization

## Documentation

See [crystal-renderer.gemmology.dev](https://crystal-renderer.gemmology.dev) for full documentation.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Related Packages

- [cdl-parser](https://github.com/gemmology-dev/cdl-parser) - Crystal Description Language parser
- [crystal-geometry](https://github.com/gemmology-dev/crystal-geometry) - 3D geometry engine
- [mineral-database](https://github.com/gemmology-dev/mineral-database) - Mineral preset database
