# pygoreadability

CPython bindings for `codeberg.org/readeck/go-readability/v2` exposing `FromString`.

## Development

Build the Go shared library for your current platform:

```bash
bash scripts/build_lib.sh
```

Then in Python:

```python
from pygoreadability import from_string

article = from_string(html, url="https://example.com")
print(article.title)
```

## Wheels

This package is designed to ship prebuilt wheels. Use `cibuildwheel` to build
platform-specific wheels for macOS arm64 and Linux x86_64.

Environment:
- `GOREADABILITY_VERSION` (optional): version/tag override (defaults to the
  version in `go/go.mod`).
- `PYGOREADABILITY_SKIP_BUILD=1` to skip the build step (expects the shared
  library to already be present in the package directory).
- `PYGOREADABILITY_AUTO_BUILD=0` to disable import-time auto-build fallback
  (useful for constrained environments).

## Null bytes

`from_string` accepts Unicode strings that may contain embedded null bytes
(`\x00`) because the binding passes explicit lengths across the FFI boundary.

Output fields are length-prefixed in the C bridge as well, so embedded null
bytes in extracted text won't be truncated.
