"""
Gemmology Plugin CLI - Command-line interface for crystal visualization.

This module provides the command-line interface for the gemmology plugin,
wrapping functionality from the component packages.
"""

import argparse
import sys


def create_argument_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        prog="gemmology",
        description="Gemmology plugin for crystal visualization and gemstone expertise",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # crystal-svg command
    svg_parser = subparsers.add_parser(
        "crystal-svg",
        aliases=["svg"],
        help="Generate SVG visualization of crystal structure",
    )
    _add_svg_arguments(svg_parser)

    # list-presets command
    list_parser = subparsers.add_parser(
        "list-presets",
        aliases=["list"],
        help="List available mineral presets",
    )
    list_parser.add_argument(
        "--category",
        "-c",
        help="Filter by category",
    )
    list_parser.add_argument(
        "--search",
        "-s",
        help="Search for presets by name",
    )

    # info command
    info_parser = subparsers.add_parser(
        "info",
        help="Show information about a preset",
    )
    info_parser.add_argument(
        "preset",
        help="Preset name (e.g., diamond, ruby, emerald)",
    )

    # version command
    subparsers.add_parser("version", help="Show version information")

    return parser


def _add_svg_arguments(parser: argparse.ArgumentParser) -> None:
    """Add SVG-related arguments to a parser."""
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--cdl",
        help="Crystal Description Language string",
    )
    group.add_argument(
        "--preset",
        "-p",
        help="Use a mineral preset (e.g., diamond, ruby)",
    )
    group.add_argument(
        "--twin",
        "-t",
        help="Twin law name (e.g., spinel, japan)",
    )

    parser.add_argument(
        "-o",
        "--output",
        help="Output file path (default: stdout)",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["svg", "png", "stl", "gltf"],
        default="svg",
        help="Output format (default: svg)",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=600,
        help="Output width in pixels (default: 600)",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=600,
        help="Output height in pixels (default: 600)",
    )
    parser.add_argument(
        "--elev",
        type=float,
        default=30.0,
        help="View elevation angle in degrees (default: 30)",
    )
    parser.add_argument(
        "--azim",
        type=float,
        default=-45.0,
        help="View azimuth angle in degrees (default: -45)",
    )
    parser.add_argument(
        "--no-axes",
        action="store_true",
        help="Hide crystallographic axes",
    )
    parser.add_argument(
        "--no-grid",
        action="store_true",
        help="Hide background grid",
    )
    parser.add_argument(
        "--info-fga",
        action="store_true",
        help="Include FGA info panel",
    )


def crystal_svg() -> None:
    """Entry point for crystal-svg command."""
    parser = argparse.ArgumentParser(
        prog="crystal-svg",
        description="Generate SVG visualization of crystal structure",
    )
    _add_svg_arguments(parser)
    args = parser.parse_args()
    _handle_svg_command(args)


def _handle_svg_command(args: argparse.Namespace) -> None:
    """Handle the crystal-svg command."""
    from crystal_geometry import cdl_to_geometry
    from crystal_renderer import generate_cdl_svg, geometry_to_gltf, geometry_to_stl
    from mineral_database import get_preset

    # Determine CDL string
    cdl: str | None = None
    preset_info = None

    if args.cdl:
        cdl = args.cdl
    elif args.preset:
        preset = get_preset(args.preset)
        if preset is None:
            print(f"Error: Unknown preset '{args.preset}'", file=sys.stderr)
            sys.exit(1)
        cdl = preset.cdl
        preset_info = preset
    elif args.twin:
        # For twins, construct the CDL with twin modifier
        cdl = f"cubic[m3m]:octahedron|twin({args.twin})"

    if cdl is None:
        print("Error: No CDL string provided", file=sys.stderr)
        sys.exit(1)

    try:
        if args.format == "svg":
            output = generate_cdl_svg(
                cdl,
                width=args.width,
                height=args.height,
                elevation=args.elev,
                azimuth=args.azim,
                show_axes=not args.no_axes,
                show_grid=not args.no_grid,
                info_panel=args.info_fga,
                preset_info=preset_info,
            )
        elif args.format in ("stl", "gltf"):
            geom = cdl_to_geometry(cdl)
            if args.format == "stl":
                output = geometry_to_stl(geom, binary=True)
            else:
                output = geometry_to_gltf(geom)
        else:
            print(f"Error: Unsupported format '{args.format}'", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Output
    if args.output:
        mode = "wb" if isinstance(output, bytes) else "w"
        with open(args.output, mode) as f:
            f.write(output)
        print(f"Written to {args.output}")
    else:
        if isinstance(output, bytes):
            sys.stdout.buffer.write(output)
        else:
            print(output)


def _handle_list_command(args: argparse.Namespace) -> None:
    """Handle the list-presets command."""
    from mineral_database import list_categories, search_presets

    if args.search:
        presets = search_presets(args.search)
    elif args.category:
        presets = search_presets(category=args.category)
    else:
        # List all categories and counts
        categories = list_categories()
        print("Available categories:")
        for cat in sorted(categories):
            presets_in_cat = search_presets(category=cat)
            print(f"  {cat}: {len(presets_in_cat)} presets")
        return

    if not presets:
        print("No presets found.")
        return

    print(f"Found {len(presets)} presets:")
    for preset in sorted(presets, key=lambda p: p.name):
        system = preset.system or "unknown"
        print(f"  {preset.name:20} ({system})")


def _handle_info_command(args: argparse.Namespace) -> None:
    """Handle the info command."""
    from mineral_database import get_preset

    preset = get_preset(args.preset)
    if preset is None:
        print(f"Error: Unknown preset '{args.preset}'", file=sys.stderr)
        sys.exit(1)

    print(f"Name: {preset.name}")
    print(f"CDL: {preset.cdl}")
    if preset.system:
        print(f"Crystal System: {preset.system}")
    if preset.chemistry:
        print(f"Chemistry: {preset.chemistry}")
    if preset.hardness:
        print(f"Hardness: {preset.hardness}")
    if preset.sg:
        print(f"Specific Gravity: {preset.sg}")
    if preset.ri:
        print(f"Refractive Index: {preset.ri}")
    if preset.birefringence:
        print(f"Birefringence: {preset.birefringence}")
    if preset.optic_sign:
        print(f"Optic Sign: {preset.optic_sign}")


def main() -> None:
    """Main entry point for the gemmology CLI."""
    parser = create_argument_parser()
    args = parser.parse_args()

    if args.command in ("crystal-svg", "svg"):
        _handle_svg_command(args)
    elif args.command in ("list-presets", "list"):
        _handle_list_command(args)
    elif args.command == "info":
        _handle_info_command(args)
    elif args.command == "version":
        from gemmology_plugin import __version__

        print(f"gemmology-plugin {__version__}")
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
