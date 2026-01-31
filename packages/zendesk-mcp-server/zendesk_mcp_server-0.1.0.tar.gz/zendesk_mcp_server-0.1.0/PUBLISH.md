# Publishing

The npm wrapper depends on the PyPI package, so **publish PyPI first**.

## 1. PyPI

```bash
# From repo root
uv build
uv publish
```

If you need to authenticate:
```bash
uv publish --token <pypi-token>
# or
export UV_PUBLISH_TOKEN=<pypi-token>
uv publish
```

## 2. npm

```bash
cd npm

# Login if needed
npm login

# Publish (--access public required for scoped packages)
npm publish --access public
```

## Version Bumps

Update version in both files before publishing:
- `pyproject.toml` - `version = "x.x.x"`
- `npm/package.json` - `"version": "x.x.x"`
