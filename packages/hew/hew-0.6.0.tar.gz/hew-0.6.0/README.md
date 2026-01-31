# Hew (Python implementation)

The Hew [changelog specification](https://codeberg.org/hew/spec) reference implementation for the Python language.

## Getting Started

Pending release to distribution channels like PyPi, you may run the program locally with `uv`.
A [nix](https://nixos.org/) devshell is present if you'd prefer to enter that managed environment with `nix develop .`.

Without nix, you will also need to obtain and install [Pandoc](https://pandoc.org/) to use the formatting translation features of `hew`.

## Usage

`hew` Python supports two primary modes of operation: as a native library and as a command-line utility.

### CLI

Use the executable command line interface if you'd like to use the Python program as a utility and work primarily with the output of the parsing results, usually JSON.

```python
uv run hew --help
```

Consult the help text to learn about supported flags and their effects.

### Library

After installing `hew` into a Python environment, instantiate the `Hewer` class with the necessary constructor arguments:

```python
Hewer(...)
```

### Validation

Clone with the submodule and use its `spec/repo-gen.sh` script along with the sibling `repo-spec.json` file to generate a sample repository with Hew-compliant changelogs and compare the results with the expected JSON results.

The `./scripts/validate.py` file is available to facilitate this process.

```shell
uv run python scripts/validate.py spec/repo-gen.sh spec/repo-spec.json
```

This will:

- Invoke `repo-gen.sh` in a temporary directory
- Run Hew inside the directory to generate a changelog manifest
- Compare it (excluding unique fields like timestamps) against the given specification JSON
- Ensure the results match the specification
