# This is a PyPi package

## Production

1. Bump the version in `pyproject.toml`
2. Run:

```bash
uv sync --all-groups --all-extras -p 3.14
uv lock -U && uv export --frozen --no-editable --no-dev -o requirements.txt > /tmp/uv.txt
rm -rf dist/* && uv build && uv publish --token $PYPI_TOKEN
```
