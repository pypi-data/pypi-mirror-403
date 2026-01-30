"""
Test suite for gemmology-plugin.

Tests the orchestration layer that combines all gemmology packages.
"""

import pytest


class TestImports:
    """Test that all re-exports work correctly."""

    def test_import_version(self):
        """Test version import."""
        from gemmology_plugin import __version__

        assert __version__ == "1.0.0"

    def test_import_cdl_parser(self):
        """Test cdl-parser re-exports."""
        from gemmology_plugin import (
            CRYSTAL_SYSTEMS,
            parse_cdl,
            validate_cdl,
        )

        assert callable(parse_cdl)
        assert callable(validate_cdl)
        assert len(CRYSTAL_SYSTEMS) == 7
        assert "cubic" in CRYSTAL_SYSTEMS

    def test_import_crystal_geometry(self):
        """Test crystal-geometry re-exports."""
        from gemmology_plugin import (
            cdl_to_geometry,
            halfspace_intersection_3d,
        )

        assert callable(cdl_to_geometry)
        assert callable(halfspace_intersection_3d)

    def test_import_mineral_database(self):
        """Test mineral-database re-exports."""
        from gemmology_plugin import (
            get_preset,
            list_categories,
            search_presets,
        )

        assert callable(get_preset)
        assert callable(search_presets)
        assert callable(list_categories)

    def test_import_crystal_renderer(self):
        """Test crystal-renderer re-exports."""
        from gemmology_plugin import (
            generate_cdl_svg,
            generate_geometry_svg,
            geometry_to_gltf,
            geometry_to_stl,
        )

        assert callable(generate_cdl_svg)
        assert callable(generate_geometry_svg)
        assert callable(geometry_to_stl)
        assert callable(geometry_to_gltf)


class TestConvenienceFunctions:
    """Test the convenience functions."""

    def test_generate_crystal_svg(self):
        """Test generate_crystal_svg convenience function."""
        from gemmology_plugin import generate_crystal_svg

        svg = generate_crystal_svg("cubic[m3m]:{111}")
        assert svg.startswith("<?xml") or svg.startswith("<svg")
        assert "</svg>" in svg

    def test_generate_preset_svg(self):
        """Test generate_preset_svg with valid preset."""
        # Skip if diamond preset not available
        from gemmology_plugin import generate_preset_svg, get_preset

        if get_preset("diamond") is None:
            pytest.skip("Diamond preset not available")

        svg = generate_preset_svg("diamond")
        assert "</svg>" in svg

    def test_generate_preset_svg_invalid(self):
        """Test generate_preset_svg with invalid preset."""
        from gemmology_plugin import generate_preset_svg

        with pytest.raises(ValueError, match="Unknown preset"):
            generate_preset_svg("not_a_real_gemstone_xyz")


class TestEndToEnd:
    """Test end-to-end pipeline."""

    def test_cdl_to_svg_pipeline(self):
        """Test full CDL to SVG pipeline."""
        from gemmology_plugin import cdl_to_geometry, generate_crystal_svg, parse_cdl

        # Parse CDL
        desc = parse_cdl("cubic[m3m]:{111}@1.0 + {100}@1.3")
        assert desc is not None

        # Generate geometry
        geom = cdl_to_geometry(desc)
        assert len(geom.vertices) > 0
        assert len(geom.faces) > 0

        # Generate SVG using convenience function
        svg = generate_crystal_svg("cubic[m3m]:{111}@1.0 + {100}@1.3")
        assert "</svg>" in svg

    def test_preset_to_stl_pipeline(self):
        """Test preset to STL pipeline."""
        from gemmology_plugin import cdl_to_geometry, geometry_to_stl, get_preset, parse_cdl

        # Get preset
        preset = get_preset("diamond")
        if preset is None:
            pytest.skip("Diamond preset not available")

        # Parse CDL from preset dict
        cdl = preset.get("cdl")
        desc = parse_cdl(cdl)
        geom = cdl_to_geometry(desc)

        # Generate STL (returns bytes)
        stl_data = geometry_to_stl(geom.vertices, geom.faces, binary=True)
        assert isinstance(stl_data, bytes)
        assert len(stl_data) > 0
        # Binary STL has 80-byte header + 4-byte facet count
        assert len(stl_data) >= 84


class TestCLI:
    """Test CLI module."""

    def test_cli_import(self):
        """Test CLI module imports."""
        from gemmology_plugin.cli import create_argument_parser, crystal_svg, main

        assert callable(main)
        assert callable(crystal_svg)
        assert callable(create_argument_parser)

    def test_argument_parser(self):
        """Test argument parser creation."""
        from gemmology_plugin.cli import create_argument_parser

        parser = create_argument_parser()
        assert parser is not None

        # Test parsing known arguments
        args = parser.parse_args(["version"])
        assert args.command == "version"

    def test_argument_parser_svg_command(self):
        """Test argument parser for crystal-svg command."""
        from gemmology_plugin.cli import create_argument_parser

        parser = create_argument_parser()
        args = parser.parse_args(["crystal-svg", "--cdl", "cubic[m3m]:{111}"])
        assert args.command == "crystal-svg"
        assert args.cdl == "cubic[m3m]:{111}"

    def test_argument_parser_svg_with_preset(self):
        """Test argument parser for crystal-svg with preset."""
        from gemmology_plugin.cli import create_argument_parser

        parser = create_argument_parser()
        args = parser.parse_args(["svg", "--preset", "diamond"])
        assert args.command == "svg"
        assert args.preset == "diamond"

    def test_argument_parser_list_command(self):
        """Test argument parser for list command."""
        from gemmology_plugin.cli import create_argument_parser

        parser = create_argument_parser()
        args = parser.parse_args(["list"])
        assert args.command == "list"

    def test_argument_parser_list_with_category(self):
        """Test argument parser for list with category."""
        from gemmology_plugin.cli import create_argument_parser

        parser = create_argument_parser()
        args = parser.parse_args(["list-presets", "--category", "cubic"])
        assert args.command == "list-presets"
        assert args.category == "cubic"

    def test_argument_parser_list_with_search(self):
        """Test argument parser for list with search."""
        from gemmology_plugin.cli import create_argument_parser

        parser = create_argument_parser()
        args = parser.parse_args(["list", "--search", "diamond"])
        assert args.command == "list"
        assert args.search == "diamond"

    def test_argument_parser_info_command(self):
        """Test argument parser for info command."""
        from gemmology_plugin.cli import create_argument_parser

        parser = create_argument_parser()
        args = parser.parse_args(["info", "diamond"])
        assert args.command == "info"
        assert args.preset == "diamond"

    def test_add_svg_arguments(self):
        """Test SVG argument helper function."""
        import argparse

        from gemmology_plugin.cli import _add_svg_arguments

        parser = argparse.ArgumentParser()
        _add_svg_arguments(parser)

        args = parser.parse_args(["--cdl", "cubic[m3m]:{111}"])
        assert args.cdl == "cubic[m3m]:{111}"
        assert args.format == "svg"  # default
        assert args.width == 600  # default
        assert args.height == 600  # default

    def test_add_svg_arguments_with_options(self):
        """Test SVG arguments with custom options."""
        import argparse

        from gemmology_plugin.cli import _add_svg_arguments

        parser = argparse.ArgumentParser()
        _add_svg_arguments(parser)

        args = parser.parse_args(
            [
                "--cdl",
                "cubic[m3m]:{111}",
                "--format",
                "stl",
                "--width",
                "800",
                "--height",
                "600",
                "--elev",
                "45",
                "--azim",
                "-30",
                "--no-axes",
                "--no-grid",
            ]
        )
        assert args.format == "stl"
        assert args.width == 800
        assert args.height == 600
        assert args.elev == 45.0
        assert args.azim == -30.0
        assert args.no_axes is True
        assert args.no_grid is True
