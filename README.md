# sg-addons

Native feature patches for [Swiftgram](https://github.com/Swiftgram/Telegram-iOS).
Upstream is pinned in `upstream.json`; sources are downloaded without history
and patched in `patches/series` order when preparing a build.

## Download

[![Add AltSource](https://img.shields.io/badge/Add_AltSource-2867B2?style=for-the-badge)](https://altdirect.app/?url=https://github.com/Applone/sg-addons/releases/latest/download/altsource.json)
[![Download Lite IPA](https://img.shields.io/badge/Download_Lite_IPA-2867B2?style=for-the-badge)](https://github.com/Applone/sg-addons/releases/latest/download/Swiftgram-lite.ipa)
[![Download Full IPA](https://img.shields.io/badge/Download_Full_IPA-2867B2?style=for-the-badge)](https://github.com/Applone/sg-addons/releases/latest/download/Swiftgram-full.ipa)

**Lite** includes the native add-ons and treats HTML message widgets as unsupported media.
**Full** also runs HTML message widgets and Python plugins. Full keeps the existing bundle
identifier. Lite uses the same identifier with a `.lite` suffix and installs separately.

## Features

- Ghost mode: hide read receipts, story views, online status, typing, and upload
  activity, with chat exceptions.
- Local message history and deleted-message retention, with an optional
  **Save disappearing media** setting for observed timed/view-once cloud photos,
  videos, and voice messages. Secret chats are excluded. The Message history
  action appears on edited messages while history capture is enabled for the
  account, and uses the chat's theme and wallpaper.
- Message filters with per-account settings and JSON import/export.
- Telegram ad blocking: hide sponsored messages and search ads, including cached
  and queued ads, without Premium. Enable **Block Telegram ads** under Swiftgram
  settings → **Additional functions** → **Telegram ads** for all accounts or an
  individual account. Changes take effect without restarting; off by default.
- Local Premium for client features, including adding, naming, and filtering
  Saved Messages tags on this device, plus local profile and badge customization.
  Local tags apply to messages available in this client and do not sync to other
  devices. Server features still require a Telegram Premium subscription.
- Python plugins with per-account activation/settings, message/send/request hooks,
  menu actions, permission-controlled Telegram sending/editing and media transfer,
  atomic updates, and safe-mode recovery. Import `.py` / `.plugin` files
  from Files under **Additional functions → Plugins**. CPython, its standard library,
  and the Swiftgram SDK ship with the IPA. Only Python source plugins are supported;
  PEP 723 metadata declares plugin details and Python requirements. Review exact
  dependency versions and PyPI links before installation; each plugin has isolated
  dependencies and Python interpreters. Compatible pure Python wheels are supported. See the
  [plugin SDK and usage guide](PLUGINS.md) and
  [Python example](examples/plugins/uppercase.py). AyuGram Python plugins require porting.

## Local message archive

Enable **Keep deleted messages** under **Additional functions**. Open a message
menu and choose **Swiftgram → View Deleted** to see saved deletions from that chat.
Tap the magnifying glass to search its text. Tap a message to see its details,
recorded edits, and available attachments. Enable **Dim deleted messages** to
make retained deletions translucent in the original chat.

Attachments use Telegram’s existing cache and expire according to its storage
settings. The archive stores message content and attachment references. An upgrade
from the earlier archive format removes its separate attachment copies while
preserving message records. Timed cloud messages also require **Save disappearing
media**, and secret chats are excluded.

Archived snapshots and their versions have a **16 MiB metadata limit per
account** and are retained for 30 days by default. Use **Swiftgram → Clear
Deleted** to remove the saved deletions for one chat, or **Clear all archives**
in **Additional functions** to clear deleted messages and edit history for the
selected account, or all signed-in accounts when using default settings. Both
actions clear local data. Logout clears the account’s archive.

## Verification

Run `just check` and `just test` after preparing the source tree. The native core
suite includes archive migration, retention, cache behavior, purge, and
session-lifecycle regressions. To run `just test-apple` on an Apple Silicon Mac,
select Xcode 27.1, install the iOS 27.0 simulator runtime for iPhone 17, prepare the
build submodules, and provide `build/configuration.json`. The Full IPA workflow runs
this suite, including the TelegramCore archive adapter and Postbox interception tests.
Lite runs the settings UI suite on the same simulator before building its IPA.
Linux core tests and Swift syntax checks do not validate iOS UI or signing.

## Build in CI

1. Add a repository secret named `BUILD_CONFIGURATION_JSON` under
   **Settings → Secrets and variables → Actions**, using the configuration below.
2. Open **Actions → Build unsigned IPA → Run workflow** and select `main`.
3. Download `sg-addons-lite-<run number>` or `sg-addons-full-<run number>` from the run's **Artifacts** section.
   It contains the IPA, dSYMs, and source provenance.

Release tags must match `v` followed by `[project].version` in `pyproject.toml`
(for example, `v1.3.0`). Update the version and run `uv lock` before tagging.
Tag validation runs before the build.
Pushing a matching tag automatically starts the same build. After a successful tag
build, the workflow publishes a GitHub Release for that tag with both IPAs, matching dSYM archives,
and the generated `altsource.json` feed, plus automatically generated
release notes. Manual runs on a tag also publish a
release; manual runs on a branch only upload the Actions artifact.

For example, to publish a version from the current commit:

```sh
git tag v1.3.0
git push origin v1.3.0
```

The workflow fetches pinned sources and submodules, applies patches, runs core
tests, and builds on macOS with the upstream Xcode version. Pushes and pull
requests run lint, patch verification, and core tests automatically.

### BuildBuddy build cache

The IPA workflow uses [BuildBuddy](https://www.buildbuddy.io/docs/quickstart/)
to share Bazel build outputs across release tags and manual runs. Both the Apple
integration suite and device build read and populate the remote cache. Tests still
execute on every run with the pinned Xcode toolchain.

Before starting a build:

1. Create a BuildBuddy account and an API key with permission to read and write
   the action cache and cached artifacts. See the
   [authentication guide](https://www.buildbuddy.io/docs/guide-auth/).
2. Add that key as the GitHub repository Actions secret `BUILDBUDDY_API_KEY`.
3. If your BuildBuddy account uses a different endpoint, set the repository Actions
   variable `BUILDBUDDY_CACHE_URL` to its `grpcs://` URL. The default is
   `grpcs://remote.buildbuddy.io`; it serves both the remote cache and build events.

The workflow requires the key and writes authenticated Bazel settings into a
temporary file on the runner. It enables compressed cache transfers and uploads
build events, with a BuildBuddy invocation link in each Bazel build/test log for
inspecting cache hits and misses.

The first build populates the cache. Later tags reuse unchanged actions while
Bazel rebuilds outputs whose inputs, configuration, or toolchain changed. No
default-branch warm-up build is needed. Reuse depends on BuildBuddy retention and
the cached outputs still being available; source preparation and submodule
downloads run as before.

## Build configuration

Use this complete JSON for the CI secret or a local configuration file.
Replace the first four values with your own; keep all keys and their types.

```json
{
  "bundle_id": "org.applone.sgaddons",
  "api_id": "12345678",
  "api_hash": "0123456789abcdef0123456789abcdef",
  "team_id": "ABCDE12345",
  "app_center_id": "",
  "is_internal_build": "true",
  "is_appstore_build": "false",
  "appstore_id": "0",
  "app_specific_url_scheme": "tg",
  "premium_iap_product_id": "",
  "enable_siri": false,
  "enable_icloud": false,
  "sg_config": ""
}
```

- `bundle_id`: your unique app identifier, such as `org.applone.sgaddons`.
- `api_id` / `api_hash`: your application credentials from
  [Telegram API development tools](https://my.telegram.org/apps).
- `team_id`: your 10-character Apple Developer Team ID from **Membership details**.

The remaining values suit an unsigned build: App Center is disabled,
`premium_iap_product_id` is an unused legacy field, and empty `sg_config` uses
Swiftgram's built-in service endpoints and bot. Keep the build flags as strings
and the Siri/iCloud flags as JSON booleans, exactly as shown.

## Build manually

Requires macOS 27, Xcode 27.1, Git, and [uv](https://docs.astral.sh/uv/).
Run from a checkout of this repository:

```sh
uv run --frozen python tools/patches.py prepare build/source --submodules
```

For Lite, apply the edition patch with `git -C build/source apply --index ../../variants/lite.patch`
and append `.lite` to the configured bundle identifier. The default source tree builds Full.

Save the configuration above as `build/configuration.json`, then run:

```sh
sudo xcode-select -s /Applications/Xcode_27.1.app/Contents/Developer
cd build/source
python3 build-system/Make/Make.py build \
  --configurationPath=../configuration.json \
  --xcodeManagedCodesigning \
  --disableProvisioningProfiles \
  --configuration=release_arm64 \
  --buildNumber=1 \
  --outputBuildArtifactsPath=../artifacts
```

Outputs are in `build/artifacts/`, relative to the repository root. Preparation
requires a new destination; use another directory if `build/source` already exists.
Both CI and manual builds produce an unsigned IPA that must be signed before
installation on a device.
