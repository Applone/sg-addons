#!/usr/bin/env bash
set -euo pipefail

source_dir="${1:-build/source}"
core_dir="$source_dir/Swiftgram/SGAdditionalCore"
temporary="$(mktemp -d "${TMPDIR:-/tmp}/sg-addons-core.XXXXXX")"
trap 'rm -rf "$temporary"' EXIT

# Apple SDKs provide SQLite3; Linux Swift toolchains need a system module map.
if [[ "$(uname -s)" == Linux ]]; then
    mkdir "$temporary/SQLite3"
    cat > "$temporary/SQLite3/module.modulemap" <<'MODULE'
module SQLite3 [system] {
    header "/usr/include/sqlite3.h"
    link "sqlite3"
    export *
}
MODULE
fi

swiftc -swift-version 5 -warnings-as-errors -D TESTING \
    -I "$temporary" \
    "$core_dir"/Sources/*.swift "$core_dir"/Tests/*.swift \
    -lsqlite3 -o "$temporary/core-checks"
"$temporary/core-checks"
