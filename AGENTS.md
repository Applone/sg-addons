# Repository Guidelines

## Project Structure

This repository maintains the sg-addons patch set for Swiftgram. `upstream.json` pins the upstream revision and expected Git trees. `patches/{build,core,ui}/` contains the tracked changes, and `patches/series` defines their application order. `variants/lite.patch` is applied after the Full series to produce Lite.

In the prepared checkout at `build/source/`, add-on code lives under `Swiftgram/SGAdditionalCore`, `Swiftgram/SGPython`, and `Swiftgram/SGSettingsUI`, with integration changes under `submodules/`. Localized strings live in `Swiftgram/SGStrings/Strings/`. Use `tools/` for build and verification tooling and `examples/plugins/` for SDK examples. Carry app changes back into the tracked patches and update `patched_tree` in `upstream.json` when the Full tree changes.

## Build and Verification

Run these commands from the repository root.

- `just check` validates the patch series and runs Ruff, strict mypy, yamllint, ShellCheck, and actionlint.
- `just prepare` fetches the pinned sources and applies the Full series to a new `build/source/` directory.
- `just test` runs the Python SDK and native core suites against prepared Full sources.
- `just test-apple` runs the Apple integration suite. Follow the manual build setup in `README.md` for the pinned Xcode, build submodules, configuration, and simulator. The README also documents the unsigned IPA build.

## Coding Style

Use four-space indentation in Swift and Python. Follow nearby code and keep upstream edits focused. Use lower camel case for Swift methods, snake case for Python functions, and descriptive kebab-case filenames for patches. Swift formatting uses `tools/swift-format.json`, Python formatting uses Ruff, and the C bridge is checked with clang-format.

## Testing

Add regressions to the existing suites. Put Python `unittest` cases in `Swiftgram/SGPython/Tests/test_*.py`, native core checks in `Swiftgram/SGAdditionalCore/Tests/`, and XCTest cases in the affected Apple module. Cover observable behavior and relevant failure paths. For Lite changes, verify that the overlay still applies and passes the Postbox import check, as CI does.

## Commits and Pull Requests

Follow Conventional Commits, using a scope when helpful, as in `fix(archive): simplify deleted message history`. In pull requests, summarize the behavior change, name the affected editions, list verification performed, and link related issues. Include screenshots for visible UI changes. Keep build credentials and generated files under `build/` out of commits.
