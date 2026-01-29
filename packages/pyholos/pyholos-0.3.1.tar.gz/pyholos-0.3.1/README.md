# PyHolos

A Python wrapper for the HOLOS 4.0 CLI - enabling estimations of Canadian agricultural greenhouse gas emissions.

## Overview

PyHolos provides a Python interface to the HOLOS CLI, allowing you to:
- Launch HOLOS simulations from Python scripts
- Model farm systems with minimal input data (PyHolos estimates missing parameters)
- Generate structured input files for the HOLOS CLI
- Process and visualize simulation results

## Features

- **Farm Modeling**: Support for livestock (beef, dairy, sheep) and land management systems (crops, carbon sequestration)
- **Data Integration**: Automatic integration with Soil Landscapes of Canada (SLC) data
- **Flexible Input**: Work with JSON configurations or pre-structured farm data
- **Post-processing**: Built-in tools for analyzing and plotting simulation results

## Requirements

- Python >= 3.12
- Dependencies: `geojson`, `shapely`, `pandas`, `pydantic`

## Installation

For detailed installation instructions including prerequisites (Git, conda, PyCharm setup),
see the [documentation](https://holos-aafc.github.io/pyholos/installation.html).

## Quick Start

```python
from pathlib import Path
from pyholos import launching

# Launch HOLOS using a JSON farm configuration
launching.launch_holos(
    path_dir_farms=Path('path/to/farm_data'),
    name_farm_json='farm.json',
    path_dir_outputs=Path('path/to/outputs'),
    id_slc_polygon=851003
)
```

See the [examples](example/extended_usage) directory for more usage patterns.

## Documentation

Full documentation is available in the [documentation](https://holos-aafc.github.io/pyholos) directory. Build it locally using Sphinx or refer to individual `.rst` files for:
- [Overview](https://holos-aafc.github.io/pyholos/overview.html)
- [Installation](https://holos-aafc.github.io/pyholos/installation.html)
- [Usage](https://holos-aafc.github.io/pyholos/usage.html)

## License

This project is licensed under the terms specified in [LICENSE](LICENSE).

## Contributing

Contributions are welcome! Please submit issues and pull requests via the [GitHub repository](https://github.com/Mon-Systeme-Fourrager/pyholos).

## Support

For questions or issues, please open an issue on the [issue tracker](https://github.com/Mon-Systeme-Fourrager/pyholos/issues).
