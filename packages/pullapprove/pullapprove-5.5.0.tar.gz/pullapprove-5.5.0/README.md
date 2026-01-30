# PullApprove

A CLI for validating and testing [PullApprove](https://www.pullapprove.com?ref=pypi) code review configurations.

## Installation

Run directly with `uvx`:

```bash
uvx pullapprove check
```

Or install globally with `uv`:

```bash
uv tool install pullapprove
```

## Usage

The CLI is available as `pullapprove` or `pa` for short.

```bash
# Create a starter CODEREVIEW.toml
pa init

# Validate configuration files
pa check

# Show files and their matching scopes
pa match
pa match --changed  # only changed files
pa match --by-scope  # organize by scope

# Calculate file coverage for review scopes
pa coverage
```

## Documentation

For full documentation, visit [pullapprove.com/docs/cli](https://5.pullapprove.com/docs/cli?ref=pypi).
