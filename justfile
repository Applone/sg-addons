check:
    uv run --frozen ruff check tools
    uv run --frozen ruff format --check tools
    uv run --frozen mypy
    uv run --frozen yamllint --strict .github .yamllint.yml
    bash -n tools/test-core.sh
    shellcheck tools/test-core.sh
    actionlint
    uv run --frozen python tools/patches.py check

prepare:
    uv run --frozen python tools/patches.py prepare build/source

test: test-python test-core

test-python source_dir="build/source":
    uv run --frozen ruff check --no-respect-gitignore "{{ source_dir }}/Swiftgram/SGPython" examples/plugins
    uv run --frozen ruff format --check --no-respect-gitignore "{{ source_dir }}/Swiftgram/SGPython" examples/plugins
    uv run --frozen mypy --strict "{{ source_dir }}/Swiftgram/SGPython/SDK" \
        "{{ source_dir }}/Swiftgram/SGPython/prepare_runtime.py" \
        "{{ source_dir }}/Swiftgram/SGPython/Tests" examples/plugins
    clang-format --dry-run --Werror "{{ source_dir }}/Swiftgram/SGPython/Bridge/SGPythonBridge.c" \
        "{{ source_dir }}/Swiftgram/SGPython/Bridge/SGPythonBridge.h"
    PYTHONPATH="{{ source_dir }}/Swiftgram/SGPython/SDK" uv run --frozen python -m unittest discover \
        -s "{{ source_dir }}/Swiftgram/SGPython/Tests" -v

test-core source_dir="build/source":
    uv run --frozen bash tools/test-core.sh "{{ source_dir }}"

# Requires the pinned Xcode and prepared build submodules on an Apple Silicon Mac.
test-apple source_dir="build/source" configuration="build/configuration.json":
    cd "{{ source_dir }}" && python3 build-system/Make/Make.py test \
        --configurationPath="{{ absolute_path(configuration) }}" \
        --xcodeManagedCodesigning --disableProvisioningProfiles --target=Tests/AllTests
