#!/usr/bin/env bash
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
build_dir=$(mktemp -d "${TMPDIR:-/tmp}/nodi-core.XXXXXX")
trap 'rm -rf "$build_dir"' EXIT
g++ -std=c++17 -Wall -Wextra -Werror -pedantic -O2 "$here/test_core.cpp" -o "$build_dir/test_core"
"$build_dir/test_core"
