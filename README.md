# sg-addons

Native feature patches for [Swiftgram](https://github.com/Swiftgram/Telegram-iOS).

## Download

<p align="center">
  <a href="https://altdirect.app/?url=https://github.com/Applone/sg-addons/releases/latest/download/altsource.json"><img src="https://altdirect.app/assets/png/AltSource_Blue.png" alt="Add AltSource" width="200"></a>
  &nbsp;
  <a href="https://github.com/Applone/sg-addons/releases/latest"><img src="https://altdirect.app/assets/png/Download_Blue.png" alt="Download IPA" width="200"></a>
</p>

- **Lite** (`Swiftgram-lite.ipa`) includes the native add-ons and displays HTML
  message widgets as unsupported media. Its `.lite` bundle ID suffix lets it
  install alongside Full.
- **Full** (`Swiftgram-full.ipa`) includes the native add-ons, HTML message
  widgets, and Python plugins. It keeps the existing bundle ID.

## Features

- **Ghost mode** hides read receipts, story views, online status, typing, and
  upload activity, with per-chat exceptions.
- **Local message history** retains edits and deletions. **Save disappearing media**
  can also retain observed timed or view-once cloud photos, videos, and voice
  messages. Secret chats are excluded.
- **Message filters** support per-account settings and JSON import/export.
- **Telegram ad blocking** hides sponsored messages and search ads without Premium.
- **Local Premium** adds on-device Saved Messages tags and local profile and badge
  customization. Server features still require Telegram Premium.
- **Python plugins** in Full support per-account settings, message hooks, and menu
  actions. Import `.py` or `.plugin` files under **Additional functions → Plugins**.
  See the [plugin SDK guide](PLUGINS.md) and [example](examples/plugins/uppercase.py).

## Build manually

Requires macOS 27, Xcode 27.1, Git, and [uv](https://docs.astral.sh/uv/).

```sh
uv run --frozen python tools/patches.py prepare build/source --submodules
```

Save this template as `build/configuration.json`. Set `bundle_id` to your app
identifier, `team_id` to your Apple Developer Team ID, and `api_id` and `api_hash`
to your [Telegram API credentials](https://my.telegram.org/apps).

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

The prepared sources build Full. For Lite, run
`git -C build/source apply --index ../../variants/lite.patch` and append `.lite`
to `bundle_id`.

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

The unsigned IPA is written to `build/artifacts/`. Sign it before installing it on a device.

## Run tests

From the repository root, prepare Full sources with `just prepare` if `build/source`
does not exist, then run:

```sh
just test
```

For the Apple integration suite, use the manual build setup on an Apple Silicon
Mac with the iOS 27.0 simulator runtime and an iPhone 17 simulator:

```sh
just test-apple
```
