# Hatchling Environment Variable Version Source

A Hatchling version source plugin that reads the version from an environment variable with a configurable fallback value,
since the built-in environment variable version source does not allow to define a fallback.

## Installation

Add the package as a build dependency to your `pyproject.toml`:

```toml
[build-system]
requires = ["hatchling", "hatch-env-plus"]
build-backend = "hatchling.build"
```

## Configuration

Configure a dynamic version source in the `project` section of `pyproject.toml`:

```toml
[project]
dynamic = ["version"]
```

Make sure you don't specify the `version` directly in the `project` section, or the dynamic version source may not be picked up.

Then, configure the version source:

```toml
[tool.hatch.version]
source = "env-plus"
variable = "PACKAGE_VERSION"  # optional, default shown
fallback = "0.0.0dev0"            # optional, default shown
```

Use the `variable` field to set the environment variable to use and set `fallback` to the desired fallback version. 

**Note: An empty version string is treated as undefined. Therefore, this will throw an error if the configured environment
variable as well as the fallback are both empty.**

## Usage

Build your project with the desired version by setting the environment variable:

```bash
PACKAGE_VERSION=2.0.0 uv build
# Builds package version "2.0.0".
```

Leave the environment variable empty to use the default:

```bash
uv build
# Builds package version 0.0.0dev0 (or configured fallback).
```
