#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
GO_DIR="$ROOT_DIR/go"
OUT_DIR="$ROOT_DIR/pygoreadability"

OS=$(uname -s)
case "$OS" in
  Darwin)
    EXT="dylib"
    ;;
  Linux)
    EXT="so"
    export CC="${CC:-gcc}"
    export CXX="${CXX:-g++}"
    ;;
  *)
    echo "unsupported OS: $OS" >&2
    exit 1
    ;;
esac

VERSION=${GOREADABILITY_VERSION:-}

pushd "$GO_DIR" >/dev/null
  if [ "$VERSION" != "" ]; then
    go get "codeberg.org/readeck/go-readability/v2@${VERSION}"
    go mod tidy
  fi
  CGO_ENABLED=1 go build -buildmode=c-shared -o "$OUT_DIR/libgoreadability.${EXT}" ./
popd >/dev/null

echo "built $OUT_DIR/libgoreadability.${EXT}"
