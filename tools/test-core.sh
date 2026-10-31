#!/usr/bin/env bash
set -euo pipefail

source_dir="$(cd "${1:-build/source}" && pwd)"
core_dir="$source_dir/Swiftgram/SGAdditionalCore"
repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SGA_PYTHON_HOME="$(python3 -c 'import sys; print(sys.base_prefix)')"
export SGA_PYTHON_HOME
export SGA_PLUGIN_EXAMPLES="$repo_dir/examples/plugins"
temporary="$(mktemp -d "${TMPDIR:-/tmp}/sg-addons-core.XXXXXX")"
trap 'rm -rf "$temporary"' EXIT

# Mirror the app bundle without installing tooling into the embedded interpreter.
export SGA_PYTHON_SDK="$temporary/python-sdk"
python3 - "$source_dir/Swiftgram/SGPython/SDK" "$SGA_PYTHON_SDK" <<'PYTHON'
import importlib.util
import shutil
import sys
import zipfile
from pathlib import Path

import certifi

source, destination = map(Path, sys.argv[1:])
shutil.copytree(source, destination)
for name in ("packaging", "resolvelib"):
    spec = importlib.util.find_spec(name)
    if spec is None or spec.origin is None:
        raise SystemExit(f"Missing test dependency: {name}")
    package = Path(spec.origin).parent
    with zipfile.ZipFile(destination / f"{name}.whl", "w") as archive:
        for file in package.rglob("*.py"):
            archive.write(file, file.relative_to(package.parent))
shutil.copy2(certifi.where(), destination / "cacert.pem")
PYTHON

# Keep new feature modules strict without reformatting the pinned upstream.
swift format lint --strict --configuration "$repo_dir/tools/swift-format.json" \
    "$core_dir/Sources/DisappearingMessages.swift" \
    "$core_dir/Sources/PluginActions.swift" \
    "$core_dir/Tests/PluginActionChecks.swift" \
    "$core_dir/Sources/PluginManifest.swift" \
    "$core_dir/Sources/PluginRegistry.swift" \
    "$core_dir/Sources/PythonPluginRuntime.swift" \
    "$core_dir/Tests/DisappearingChecks.swift" \
    "$core_dir/Tests/PluginChecks.swift" \
    "$core_dir/Tests/PythonPluginChecks.swift" \
    "$source_dir/submodules/TelegramCore/Sources/AdditionalFunctions/AdditionalDisappearingMedia.swift" \
    "$source_dir/submodules/TelegramCore/Sources/AdditionalFunctions/AdditionalPluginActions.swift" \
    "$source_dir/submodules/TelegramCore/Sources/AdditionalFunctions/AdditionalPlugins.swift" \
    "$source_dir/Swiftgram/SGSettingsUI/Sources/AdditionalPlugins.swift"

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

python_include="$(python3 -c 'import sysconfig; print(sysconfig.get_path("include"))')"
python_libdir="$(python3 -c 'import sysconfig; print(sysconfig.get_config_var("LIBDIR"))')"
python_library="$(python3 -c 'import sysconfig; print(sysconfig.get_config_var("LDLIBRARY"))')"
mkdir "$temporary/SGPythonBridge"
cat > "$temporary/SGPythonBridge/module.modulemap" <<MODULE
module SGPythonBridge {
    header "$source_dir/Swiftgram/SGPython/Bridge/SGPythonBridge.h"
    export *
}
MODULE
clang -std=c11 -Wall -Wextra -Werror -isystem "$python_include" \
    -c "$source_dir/Swiftgram/SGPython/Bridge/SGPythonBridge.c" -o "$temporary/python-bridge.o"

swiftc -swift-version 5 -warnings-as-errors -D TESTING \
    -I "$temporary" \
    "$core_dir"/Sources/*.swift "$core_dir"/Tests/*.swift \
    "$temporary/python-bridge.o" "$python_libdir/$python_library" \
    -Xlinker -rpath -Xlinker "$python_libdir" -lsqlite3 -o "$temporary/core-checks"
"$temporary/core-checks"
