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

test:
    bash tools/test-core.sh build/source
