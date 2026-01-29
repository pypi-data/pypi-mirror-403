# Container Detect

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](https://github.com/ysskrishna/container-detect/blob/main/LICENSE)
![Tests](https://github.com/ysskrishna/container-detect/actions/workflows/test.yml/badge.svg)
[![PyPI](https://img.shields.io/pypi/v/container-detect)](https://pypi.org/project/container-detect/)
[![PyPI Downloads](https://static.pepy.tech/personalized-badge/container-detect?period=total&units=INTERNATIONAL_SYSTEM&left_color=GREY&right_color=BLUE&left_text=downloads)](https://pepy.tech/projects/container-detect)

Detect if your Python process is running inside a container. Supports Docker, Podman, Kubernetes, containerd, LXC, and more. Inspired by the popular [is-inside-container](https://github.com/sindresorhus/is-inside-container) npm package. Supports cached results with optional refresh.

## Features

- Fast and reliable container detection for multiple container types
- Supports Docker, Podman, Kubernetes, containerd, LXC, and more
- Multiple detection methods for robustness
- Cached results for performance optimization
- Zero dependencies, minimal overhead
- Type hints for better IDE support
- Graceful error handling

## Supported Container Types

- **Docker** - Classic Docker containers
- **Podman** - Podman containers
- **Kubernetes** - Kubernetes pods
- **containerd** - containerd containers
- **LXC** - Linux Containers
- **CRI-O** - Container Runtime Interface
- **AWS ECS** - Amazon Elastic Container Service
- And more container runtimes

## Installation

```bash
pip install container-detect
```

Or using `uv`:

```bash
uv add container-detect
```

## Usage

### Check if running inside a container

```python
from container_detect import is_inside_container

if is_inside_container():
    print("Running inside a container")
else:
    print("Not running inside a container")
```

### Force refresh cache

```python
from container_detect import is_inside_container

# Use cached result (default)
is_inside_container()  # Fast, uses cache

# Force a fresh check, bypassing cache
is_inside_container(force_refresh=True)  # Performs new detection
```



## Credits

This package is inspired by the [is-inside-container](https://github.com/sindresorhus/is-inside-container) ([npm](https://www.npmjs.com/package/is-inside-container)) npm package by [Sindre Sorhus](https://github.com/sindresorhus).

## Changelog

See [CHANGELOG.md](https://github.com/ysskrishna/container-detect/blob/main/CHANGELOG.md) for a detailed list of changes and version history.

## Contributing

Contributions are welcome! Please read our [Contributing Guide](https://github.com/ysskrishna/container-detect/blob/main/CONTRIBUTING.md) for details on our code of conduct, development setup, and the process for submitting pull requests.

## Support

If you find this library useful, please consider:

- ⭐ **Starring** the repository on GitHub to help others discover it.
- 💖 **Sponsoring** to support ongoing maintenance and development.

[Become a Sponsor on GitHub](https://github.com/sponsors/ysskrishna) | [Support on Patreon](https://patreon.com/ysskrishna)

## License

MIT License - see [LICENSE](https://github.com/ysskrishna/container-detect/blob/main/LICENSE) file for details.

## Author

**Y. Siva Sai Krishna**

- GitHub: [@ysskrishna](https://github.com/ysskrishna)
- LinkedIn: [ysskrishna](https://linkedin.com/in/ysskrishna)
