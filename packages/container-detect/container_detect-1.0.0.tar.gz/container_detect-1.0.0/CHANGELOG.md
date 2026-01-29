# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0]

### Added
- Initial release of container-detect Python package
- `is_inside_container()` function to check if the current process is running inside a container
- Linux-only detection using multiple methods:
  - Check for `/.dockerenv` file existence (Docker classic, some Podman)
  - Check for `/.containerenv` and `/run/.containerenv` files (Podman)
  - Check `/proc/self/cgroup` and `/proc/1/cgroup` for container keywords (Docker, Kubernetes, containerd, Podman, LXC, etc.)
  - Check `/proc/self/mountinfo` for container filesystem patterns
  - Check environment variables (KUBERNETES_SERVICE_HOST, KUBERNETES_PORT, container, DOCKER_CONTAINER, PODMAN_CONTAINER, ECS_CONTAINER_METADATA_URI)
- `force_refresh` parameter to bypass cache and perform fresh detection
- LRU cache optimization for repeated calls using `functools.lru_cache`
- Type hints for better IDE support and type checking
- Zero dependencies for minimal overhead
- Comprehensive test suite with unit tests covering all detection methods and edge cases
- Python 3.8+ compatibility

### Features
- Fast and reliable container detection for multiple container types
- Supports Docker, Podman, Kubernetes, containerd, LXC, and more
- Multiple detection methods for robustness
- Cached results for performance optimization
- Linux platform support
- Graceful error handling for file system operations
- Case-insensitive keyword matching in cgroup files

[1.0.0]: https://github.com/ysskrishna/container-detect/releases/tag/v1.0.0
