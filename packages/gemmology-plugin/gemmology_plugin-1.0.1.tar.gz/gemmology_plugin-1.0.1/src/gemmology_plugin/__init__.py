"""
Gemmology Plugin - Claude Code plugin for coloured gemstone expertise.

This package provides comprehensive tools for gemmology and crystallography,
including crystal structure visualization, gemstone identification, and
FGA-curriculum aligned reference materials.

Example:
    Generate a crystal visualization:

    >>> from gemmology_plugin import generate_crystal_svg
    >>> svg = generate_crystal_svg("cubic[m3m]:{111}")

    Get preset information:

    >>> from gemmology_plugin import get_preset
    >>> ruby = get_preset("ruby")
    >>> print(ruby.ri)
    '1.762-1.770'
"""

__version__ = "1.0.0"
__author__ = "Fabian Schuh"
__email__ = "fabian@gemmology.dev"

# Re-export core functionality from component packages
from cdl_parser import (
    CRYSTAL_SYSTEMS,
    NAMED_FORMS,
    POINT_GROUPS,
    TWIN_LAWS,
    CrystalDescription,
    CrystalForm,
    MillerIndex,
    Modification,
    parse_cdl,
    validate_cdl,
)
from crystal_geometry import (
    CrystalGeometry,
    cdl_to_geometry,
    halfspace_intersection_3d,
)
from crystal_renderer import (
    generate_cdl_svg,
    generate_geometry_svg,
    geometry_to_gltf,
    geometry_to_stl,
)
from mineral_database import (
    Mineral,
    get_preset,
    search_presets,
)
from mineral_database import (
    list_preset_categories as list_categories,
)

__all__ = [
    # Version info
    "__version__",
    # CDL Parser
    "parse_cdl",
    "validate_cdl",
    "CrystalDescription",
    "CrystalForm",
    "MillerIndex",
    "Modification",
    "CRYSTAL_SYSTEMS",
    "POINT_GROUPS",
    "TWIN_LAWS",
    "NAMED_FORMS",
    # Crystal Geometry
    "cdl_to_geometry",
    "CrystalGeometry",
    "halfspace_intersection_3d",
    # Mineral Database
    "get_preset",
    "search_presets",
    "Mineral",
    "list_categories",
    # Crystal Renderer
    "generate_cdl_svg",
    "generate_geometry_svg",
    "geometry_to_stl",
    "geometry_to_gltf",
]


def generate_crystal_svg(
    cdl: str,
    *,
    elevation: float = 30.0,
    azimuth: float = -45.0,
    show_axes: bool = True,
    show_grid: bool = True,
    info_properties: dict = None,
) -> str:
    """
    Generate an SVG visualization of a crystal from CDL notation.

    This is a convenience function that combines parsing, geometry generation,
    and rendering in a single call.

    Args:
        cdl: Crystal Description Language string (e.g., "cubic[m3m]:{111}")
        elevation: View elevation angle in degrees
        azimuth: View azimuth angle in degrees
        show_axes: Whether to show crystallographic axes
        show_grid: Whether to show background grid
        info_properties: Dict of properties to show in info panel

    Returns:
        SVG string

    Example:
        >>> svg = generate_crystal_svg("cubic[m3m]:{111}@1.0 + {100}@1.3")
        >>> with open("crystal.svg", "w") as f:
        ...     f.write(svg)
    """
    import os
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as f:
        output_path = f.name

    try:
        generate_cdl_svg(
            cdl,
            output_path,
            elev=elevation,
            azim=azimuth,
            show_axes=show_axes,
            show_grid=show_grid,
            info_properties=info_properties,
        )
        with open(output_path) as f:
            return f.read()
    finally:
        if os.path.exists(output_path):
            os.unlink(output_path)


def generate_preset_svg(
    preset_name: str,
    *,
    elevation: float = 30.0,
    azimuth: float = -45.0,
    show_axes: bool = True,
    show_grid: bool = True,
    info_panel: bool = True,
) -> str:
    """
    Generate an SVG visualization of a preset gemstone.

    Args:
        preset_name: Name of the preset (e.g., "diamond", "ruby", "emerald")
        elevation: View elevation angle in degrees
        azimuth: View azimuth angle in degrees
        show_axes: Whether to show crystallographic axes
        show_grid: Whether to show background grid
        info_panel: Whether to include FGA info panel (default True for presets)

    Returns:
        SVG string

    Example:
        >>> svg = generate_preset_svg("diamond", info_panel=True)
    """
    preset = get_preset(preset_name)
    if preset is None:
        raise ValueError(f"Unknown preset: {preset_name}")

    # Get CDL string from preset dict
    cdl = preset.get("cdl")
    if not cdl:
        raise ValueError(f"Preset '{preset_name}' has no CDL definition")

    # Build info properties from preset if info_panel is True
    info_props = None
    if info_panel:
        info_props = {
            "name": preset.get("name", preset_name),
            "chemistry": preset.get("chemistry"),
            "system": preset.get("system"),
            "hardness": preset.get("hardness"),
            "ri": preset.get("ri"),
            "sg": preset.get("sg"),
        }
        # Remove None values
        info_props = {k: v for k, v in info_props.items() if v is not None}

    return generate_crystal_svg(
        cdl,
        elevation=elevation,
        azimuth=azimuth,
        show_axes=show_axes,
        show_grid=show_grid,
        info_properties=info_props,
    )
