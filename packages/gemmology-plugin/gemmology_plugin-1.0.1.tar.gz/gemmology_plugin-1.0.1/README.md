# Gemmology Plugin

A Claude Code plugin for coloured gemstone expertise and crystal visualization.

Part of the [Gemmology Project](https://gemmology.dev).

## Features

- **Crystal Visualization**: Generate SVG, STL, and glTF visualizations of crystal structures
- **Mineral Database**: Access FGA-curriculum aligned gemstone data for 50+ minerals
- **CDL Parser**: Parse and validate Crystal Description Language notation
- **Gem Identification**: Interactive workflow for systematic gemstone identification

## Installation

```bash
pip install gemmology-plugin
```

This installs the core plugin along with all component packages:
- `cdl-parser` - Crystal Description Language parser
- `mineral-database` - Gemstone property database
- `crystal-geometry` - 3D crystal geometry engine
- `crystal-renderer` - SVG/STL/glTF visualization

### Optional: Language Server

For editor integration with CDL syntax highlighting and completion:

```bash
pip install gemmology-plugin[lsp]
```

## Quick Start

### Command Line

```bash
# Generate crystal visualization
gemmology crystal-svg --preset diamond -o diamond.svg

# List available presets
gemmology list-presets

# Get mineral information
gemmology info ruby
```

### Python API

```python
from gemmology_plugin import generate_crystal_svg, get_preset

# Generate from CDL notation
svg = generate_crystal_svg("cubic[m3m]:{111}@1.0 + {100}@1.3")

# Generate from preset
ruby = get_preset("ruby")
svg = generate_crystal_svg(ruby['cdl'], info_properties={'name': ruby['name']})
```

## Claude Code Plugin

When used as a Claude Code plugin, this package provides:

### Commands

- `/crystal-svg` - Generate crystal structure visualizations
- `/identify-gem` - Interactive gemstone identification workflow

### Agents

Expert agents for domain-specific tasks:
- `crystallography-expert` - Crystal systems, symmetry, Miller indices
- `gemmology-expert` - Gemstone properties, FGA data
- `cdl-expert` - CDL syntax and parsing

### Skills

Reference skills covering FGA curriculum topics:
- Physical properties (hardness, SG, cleavage)
- Optical properties (RI, birefringence, dispersion)
- Inclusions and fingerprints
- Treatments and enhancements
- Synthetics and simulants
- Origin determination

## CDL Syntax Overview

Crystal Description Language (CDL) provides precise control over crystal morphology:

```
system[point_group]:{form}@distance + {form}@distance
```

Examples:
```
cubic[m3m]:{111}                    # Octahedron
cubic[m3m]:{111}@1.0 + {100}@1.3    # Truncated octahedron
trigonal[-3m]:{10-10}@1.0 + {0001}@0.5  # Quartz prism
```

## Component Packages

This plugin integrates:

| Package | Description |
|---------|-------------|
| [cdl-parser](https://github.com/gemmology-dev/cdl-parser) | CDL parsing and validation |
| [mineral-database](https://github.com/gemmology-dev/mineral-database) | Gemstone property database |
| [crystal-geometry](https://github.com/gemmology-dev/crystal-geometry) | 3D geometry generation |
| [crystal-renderer](https://github.com/gemmology-dev/crystal-renderer) | Visualization and export |
| [cdl-lsp](https://github.com/gemmology-dev/cdl-lsp) | Language server (optional) |

## Development

```bash
git clone https://github.com/gemmology-dev/gemmology-plugin
cd gemmology-plugin
pip install -e ".[dev]"
pytest tests/ -v
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Links

- [Documentation](https://gemmology.dev/docs)
- [CDL Specification](https://gemmology.dev/cdl)
- [GitHub Repository](https://github.com/gemmology-dev/gemmology-plugin)
