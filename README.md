# sg-addons

Native feature patches for [Swiftgram](https://github.com/Swiftgram/Telegram-iOS).
Upstream is pinned in `upstream.json`; sources are downloaded without history
and patched in `patches/series` order when preparing a build.

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

Enable **Keep deleted messages** under **Additional functions** to capture cloud
messages observed by this client. **Deleted messages** opens a searchable archive
from settings or a chat menu, including archived chats no longer available in the
live chat list. Search supports message-type filters and a saved-before UTC date.
Recorded edits, copy actions, attachment status, and locally saved file previews
are available from each archived entry. **Captured chats** lists stored peers
independently of current membership; turn off **Show deleted messages only** to
view their other captured messages. Voice attachments use Telegram's local audio
player with play, pause, and seek controls. Archived details include reply and
forward metadata. Spoilers stay masked until **Show spoilers** is enabled. Open a
recorded version to inspect its own media attachments. Attachment status refreshes
when a download completes.

Archive files live outside Telegram's ordinary cache. Clearing that cache does
not remove them. Explicit message/chat deletion and archive purge remove the
corresponding saved content; logout removes the account's archive and legacy
history. Purge markers prevent a later history refresh from restoring explicitly
purged entries. Disabling capture preserves already archived content.

The defaults are 30 days, 1 GiB per account, a 100 MiB per-file limit, and downloads
over Wi-Fi. Cached attachments are copied when available. The oldest archived
messages are evicted when the quota is exceeded. Archive settings expose these
limits, attachment download status, bot capture, and per-chat overrides. New
profiles exclude bot dialogs; existing profiles preserve their previous behavior.
Timed cloud media still requires **Save disappearing media**. Secret chats are
excluded. iOS background suspension and unavailable server files can prevent media
capture.

Legacy metadata is migrated in restartable batches. Cached originals are copied
when available; entries whose original content is missing are labeled explicitly.
No message or attachment that the client never received can be recovered.

## Verification

Run `just check` and `just test` after preparing the source tree. The native core
suite includes archive migration, retention, attachment ownership, purge, and
session-lifecycle regressions. On an Apple Silicon Mac with the pinned Xcode and
prepared build submodules, run `just test-apple` with `build/configuration.json` in
place. It runs the upstream Apple suite, including TelegramCore archive adapter
and Postbox interception checks. The IPA workflow runs that suite before building the device artifact.
Linux core tests and Swift syntax checks do not validate iOS UI or signing.

## Build in CI

1. Add a repository secret named `BUILD_CONFIGURATION_JSON` under
   **Settings → Secrets and variables → Actions**, using the configuration below.
2. Open **Actions → Build unsigned IPA → Run workflow** and select `main`.
3. Download `sg-addons-unsigned-<run number>` from the run's **Artifacts** section.
   It contains the IPA, dSYMs, and source provenance.

Release tags must match `v` followed by the version in `release-version` (for example,
`v1.1.2`). Update that manifest before tagging. Tag validation runs before the build.
Pushing a matching tag automatically starts the same build. After a successful tag
build, the workflow publishes a GitHub Release for that tag with only
`Swiftgram.ipa` and `Swiftgram.DSYMs.zip` as assets, plus automatically generated
release notes. Manual runs on a tag also publish a
release; manual runs on a branch only upload the Actions artifact.

For example, to publish a version from the current commit:

```sh
git tag v1.1.2
git push origin v1.1.2
```

The workflow fetches pinned sources and submodules, applies patches, runs core
tests, and builds on macOS with the upstream Xcode version. Pushes and pull
requests run lint, patch verification, and core tests automatically.

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

Requires macOS 26, Xcode 26.6, Git, and [uv](https://docs.astral.sh/uv/).
Run from a checkout of this repository:

```sh
uv run --frozen python tools/patches.py prepare build/source --submodules
```

Save the configuration above as `build/configuration.json`, then run:

```sh
sudo xcode-select -s /Applications/Xcode_26.6.app/Contents/Developer
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
