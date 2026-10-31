# Swiftgram Python plugins, SDK 1.1

Swiftgram embeds CPython and a small native-facing Python SDK. Plugins are real
Python source files, with functions, classes, loops, and supported standard-library
imports. Install `.py` or `.plugin` files from **Additional functions → Plugins**.
Only Python source files are accepted. See the [complete example](examples/plugins/uppercase.py).

## Metadata and dependency review

Plugins use a UTF-8 [PEP 723 script block](https://packaging.python.org/en/latest/specifications/inline-script-metadata/).
Inspection parses TOML and Python syntax without importing or executing plugin code.
`dependencies` contains PEP 508 requirements, and `requires-python` uses PEP 440
version specifiers against the embedded Python version. Both are optional;
dependencies default to empty and an omitted Python constraint accepts the runtime.

Put display information and SDK registrations in `[tool.swiftgram]`. `id` and
`name` are required; `version` defaults to `1.0`. Optional fields are `author`,
`description`, `sdk-version`, `app-version`, `permissions`, `hooks`, `settings`,
and `menus`. The extension also accepts these fields directly in the script
block, but rejects duplicate definitions across the two locations. Unknown
Swiftgram fields are errors. Standard `[tool]` namespaces for other tools are
allowed. Use standard TOML values, including `true`/`false` rather than Python's
`True`/`False`.

```python
# /// script
# requires-python = ">=3.12"
# dependencies = ["requests>=2.32,<3"]
# [tool.swiftgram]
# id = "example"
# name = "Example plugin"
# version = "1.0"
# author = "Example author"
# description = "Shows metadata and dependency declarations."
# permissions = ["outgoingMessages"]
# hooks = [{ event = "sendMessage", name = "send_message" }]
# ///

from swiftgram import BasePlugin, HookResult, HookStrategy

class Plugin(BasePlugin):
    def on_send_message(self, event):
        return HookResult(HookStrategy.MODIFY, text=event.text.upper())
```

The [dependency-free example](examples/plugins/uppercase.py) can be imported offline.
Legacy `__permissions__`, `__hooks__`, `__settings__`, `__menus__`,
`__sdk_version__`, and `__app_version__` literal assignments remain supported for
SDK registrations. New plugins should put them in TOML. A field cannot be defined
in both places. Identity and display information come only from TOML;
`__id__`, `__name__`, `__version__`, `__author__`, and `__description__` are rejected,
as are `__requirements__` and other legacy dependency assignments. Previously
installed plugins keep their sources and settings, but legacy metadata is marked
incompatible until an updated PEP 723 source is imported and reviewed.

Importing opens separate labeled fields for name, ID, version, author, description,
and Python compatibility, followed by requested permissions and the code trust
notice. Updates show the installed and proposed plugin versions. Resolution starts
in the background; **Install** appears only when a complete dependency review is
ready. **Dependencies** opens every direct and transitive package with its exact
version, wheel filename and SHA-256, and a link to that release on PyPI. The same
list is available from installed-plugin settings. **Decline installation** discards
the review without installing packages or executing plugin code.

The manager uses build-pinned `packaging` for requirements, versions and markers,
and `resolvelib` for backtracking resolution against PyPI's HTTPS Simple JSON API.
It evaluates extras and environment markers for the embedded runtime, excludes
yanked files, and accepts prereleases only when the specifier explicitly admits
them. Conflicting constraints or unavailable compatible wheels prevent installation.
Only named PyPI requirements are supported: direct URLs, VCS repositories, local
paths, alternate indexes, source distributions, build backends and on-device native
extension installation are disabled. iOS dependencies must have compatible
`py*-none-any` wheels. Wheels with native libraries, `.pth` hooks, external data,
headers or standalone scripts are rejected.

Resolution downloads and verifies PEP 658 metadata; when unavailable, it reads
metadata from the hash-verified wheel. It never runs package setup code. A review
binds the source to the full package closure and exact artifact hashes in manager
memory, expires after 30 minutes, and can be used only once in its original registry.
Closing or declining a review discards it. Expired reviews and failed installations
require a fresh review. Installation fetches only the approved artifacts, checks
SHA-256 and equality with the reviewed metadata, and never resolves again. Changing
or disappearing artifacts fail installation without substituting a different version.
TLS uses a build-pinned certificate bundle supplied with the IPA.

Files must be at most 256 KB. IDs use 2–32 ASCII characters: a letter first,
followed by letters, digits, `_`, or `-`. Names are nonblank and at most 120 UTF-8
bytes. Plugin versions have 1–4 numeric components, each from 0 to 999999.
Optional SDK/app constraints use `>=`, `<=`, `==`, `>`, or `<` followed by a numeric
version; missing components compare as zero. SDK version is `1.1`. Author and
description limits are 120 and 2048 UTF-8 bytes. At most 64 plugins and 32 MB of
registry data are allowed. Requirements are limited to 64 strings of 512 characters;
resolution visits at most 64 projects and 1000 rounds, with a 90-second operation
budget and 15-second network socket timeout. Individual wheel downloads are limited
to 32 MB; cumulative downloads and an expanded installation to 128 MB each.

Each hook declares `event`, `name`, and optional `substring`, `priority`, and
`callback`. Arrays default to empty, with at most 32 hooks, 32 settings, and 16
menus. Event names are case sensitive; matching is exact unless `substring` is
`true`. Priorities range from -1000 to 1000. Plugins run in descending matching
priority, with IDs breaking ties in ascending order. Each plugin runs once, using
its highest matching hook, then declaration order. Conditions, text construction,
and result strategies belong in Python callbacks. Callback names must be ASCII
Python identifiers of at most 64 bytes.

## Dependency and interpreter isolation

Each installation gets a newly created UUID environment under the app's private
plugin directory. There is no shared plugin `site-packages`, global pip environment,
or package ownership counter. Updates create a separate environment; they do not
write into the previous installation. Archive traversal, symlinks, case-insensitive
file collisions, SDK replacements and standard-library replacements are rejected.
A per-installation lock records the reviewed dependency artifacts and installed file
hashes. Activation verifies its package list and files before executing the plugin.
Python bytecode files are not written into installed environments.

Each enabled plugin/account uses its own CPython subinterpreter with an independent
`sys.modules`, SDK objects, source module, dependency imports and search path. Two
plugins can import different versions of the same package without replacing each
other's modules. The manager's packaging/resolver tooling is loaded only in its
own interpreter, so it does not dictate a plugin's `packaging` version. Disabling
or replacing a plugin destroys its account interpreter. Threads, fork and exec are
disabled in plugin subinterpreters; native imports must support multiple interpreters.
The IPA supplies its pinned CPython and signed standard-library frameworks; it
excludes system/user site packages, `ensurepip`, `venv`, and environment-variable
path discovery.

Installation stages all packages before changing the registry. Registry persistence
failure or activation failure restores the previous source, environment, settings
and desired enablement. Successful updates and removals delete the retired
environment. Interrupted operations enter safe mode; a crash before registry commit
can leave an unused environment on disk. Reset preserves the original registry as
a backup, so its unused environments are retained for inspection.

This isolates dependency installation and Python module state. Trusted plugins
still run inside the application process with available filesystem and network
access. It is not a security sandbox against hostile plugins: deliberate filesystem
writes, native calls and process-wide side effects cannot be contained or rolled
back. SDK permissions control host callbacks. Install only trusted code.

| Permission | SDK access |
| --- | --- |
| `incomingMessages` | Read, change, or suppress locally displayed cloud-message text; read message menu context |
| `outgoingMessages` | Change or cancel composed cloud-message text and media captions |
| `network` | Cancel named requests and change existing terminal error descriptions |
| `menus` | Add native copy and information actions |

Permissions may not repeat. Hooks require the corresponding permission; message
menus require both `menus` and `incomingMessages`.

Define `class Plugin(BasePlugin)`. Each enabled account receives its own instance
and interpreter namespace. `self.account` is the host account ID and
`self.settings` contains that account's typed setting values. Changes to declared
setting values are validated and persisted after successful callbacks. Host objects
are not passed into Python; events are copied values with `kind`, `name`,
`account`, `chat`, `text`, and `error` fields.

| Registration event | Default method |
| --- | --- |
| `message` | `on_message(event)` |
| `sendMessage` | `on_send_message(event)` |
| `preRequest` | `pre_request_hook(event)` |
| `postRequest` | `post_request_hook(event)` |
| Menu action | `on_menu(event, menu_id)` |

Hook methods return `None` or `HookResult`. Strategies are `DEFAULT`, `MODIFY`,
`MODIFY_FINAL`, and `CANCEL`; supply `text=` for message replacements or `error=`
for an existing request error. Pre-request hooks support only default/cancel.
Post-request hooks cannot cancel, replace typed responses, or turn success into an
error. Menu methods return text for the menu's declared native action. The host
validates output size, outgoing text limits, settings, and callback permissions.

`on_plugin_load()` initializes the account instance. `on_plugin_unload()` releases
plugin-owned resources. Repeated activation does not duplicate instances. Updates
validate metadata before replacement; activation/import failures attempt to restore
previous source and activation. Files/settings are atomically persisted, but
arbitrary Python side effects cannot be rolled back. Disabling, uninstalling, safe
mode, and errors remove active host registrations.

## Settings, menus, and installation

Settings are literal dictionaries in `__settings__`:

```python
__settings__ = [
    {"key": "caption", "title": "Caption", "defaultValue": "Sent with Swiftgram"},
    {"key": "enabled", "title": "Enabled", "defaultValue": True},
]
```

Keys follow plugin ID syntax and must be unique. Titles are nonempty and at most
120 UTF-8 bytes. Defaults define the type: `bool`, `int`, or `str`. Integers are
limited to ±1000000; text to 2048 UTF-8 bytes. Text settings may declare `choices`
with 1–20 unique strings, each at most 120 UTF-8 bytes, including the default.
The manager displays switches, inputs, or selection sheets as appropriate.
Unknown keys, changed types, and values outside choices are rejected. Settings
persist per plugin/account across disable and restart.

Menus declare a native location and action, with their text supplied by Python:

```python
__menus__ = [
    {"id": "copy", "title": "Copy text", "location": "message", "action": "copyText"},
]
```

Locations are `message` and `settings`; actions are `copyText` and `showText`.
IDs follow plugin ID syntax and must be unique. Titles are nonempty and at most
120 UTF-8 bytes. `callback` optionally overrides `on_menu`. The callback receives
the copied event and menu ID, and returns text up to 64 KB. Settings-menu context
has empty text and no chat. Menu order is plugin ID followed by declaration order.
Selection rechecks activation, location, and ownership, so a stale item cannot
execute after disable, removal, or safe-mode entry.

Import a `.py` or `.plugin` source file through Files, review its metadata,
permissions, code-trust notice and complete resolved dependency list, then install it. Installation is app-wide; new plugins start
disabled and activation is per account. Files have no signature or publisher
verification. Open an installed plugin to enable it, edit settings, or remove it.
Save commits setting edits. Added permissions disable an updated plugin for every
account until explicitly enabled again. Compatible settings survive updates;
removed keys and changed types return to defaults. Removal deletes installation
and settings for every account. Previously processed or sent messages are not
rolled back.

Hook output is limited to 64 KB. Outgoing text is additionally limited to 4096
UTF-16 code units; request error descriptions to 512 UTF-8 bytes. Oversized input
skips dispatch. A failed callback preserves the preceding event, records the
failure, disables the plugin's callbacks, and lets later plugins continue.
Enabling the plugin explicitly retries it.

The incoming hook runs on cloud insertions/text changes after archiving the host's
original observation; attribute-only updates with unchanged text skip it. Changed
text clears original text entities. Outgoing forwards and secret/local messages
are excluded. Cancellation preserves result positions in mixed outgoing batches.
Pre-request cancellation returns local error `406 / SWIFTGRAM_PLUGIN_CANCELLED`.
Post-request hooks cannot replace typed responses, change error codes, or turn
successful responses into errors. Raw Telegram update bookkeeping stays with the
host.

## Execution and recovery

Plugin CPython calls run on a serial native worker with GIL coordination.
Package management has its own worker and manager thread state, so network waits
do not occupy the callback worker. The host waits at most 250 ms for hook/menu
calls, two seconds for inspection/lifecycle work, ten seconds for environment
verification, and 120 seconds for package resolution/installation.
Python tracing provides an earlier cooperative deadline for normal Python code.
Native extension calls and deliberately altered tracing cannot be forcibly stopped
safely; a host timeout quarantines the interpreter until application restart,
preserves the current host event, and leaves recovery available in native UI.
Queued calls whose deadline already expired are not executed.

An independent invocation marker is written before interpreter work. An interrupted
call causes safe mode on restart. Recovery can inspect/remove plugins without
executing them. The native manager stays reachable even if the Python worker is
stuck. These mechanisms do not make Python a sandbox or terminate arbitrary
plugin-created threads.

AyuGram's Java/Android imports and method hooks require porting to Swiftgram's
explicit host API. Android plugin-file compatibility is not claimed.

## Verification

Python tests cover non-executing TOML inspection, backtracking, conflicting
constraints, extras/markers, pinned artifact installation, hash and metadata checks,
archive paths/collisions, cancellation/expiry and isolated environments. A compiled
C bridge regression verifies conflicting module versions, independent standard-library
module state, and interpreter destruction/recreation. Native core checks exercise
the Swift/C/Python boundary, settings, menus, updates, rollback and missing imports. Run `just test` after source preparation, or
`just test-python` for the Python SDK checks alone. Both `test-python` and
`test-core` accept an optional prepared source directory. Native checks
need Swift, Clang, and Python 3.12+ with development headers and a shared library.

The iOS framework, UIKit, signing, and device lifecycle still require macOS/iOS
verification; Linux checks do not establish those properties.


## SDK 1.1: Telegram actions and media

Declare `sdk-version = ">=1.1"` in `[tool.swiftgram]`. The existing SDK 1.0
callbacks remain available; exact version constraints continue to be enforced.
New permissions appear individually in installation review. Adding permissions to
an update disables it until the user explicitly re-enables it.

| Permission | Additional access |
| --- | --- |
| `readMessages` | Detailed event snapshots and explicit message lookup |
| `sendMessages` | Send/reply in accessible cloud chats |
| `editMessages` | Edit your own message text and captions |
| `downloadMedia` | Download ordinary attachments; also requires `readMessages` |
| `sendMedia` | Send photos, videos and documents; also requires `sendMessages` |

Actions are bound to the plugin's enabled account. Chat identifiers keep the
existing `user:123`, `chat:123`, and `channel:123` syntax. Secret chats are excluded.
The native adapters use Telegram's existing access checks and outbox; declaring
permissions does not confer Telegram administrator rights.

`event.message` is an optional snapshot dictionary with `id`, `sender`,
`timestamp`, `replyTo`, `threadID`, `text`, `entities`, and `attachments` fields.
Message IDs are integers, and the outgoing ID is absent until assigned. Attachment
summaries contain an opaque `id`, `kind`, and optional filename, MIME type and size.
Snapshots are visible only with `readMessages`; existing text/chat fields retain
their previous behavior. `event.plugin_origin` identifies plugin-generated sends.

Methods on `BasePlugin` return an action ID immediately:

```python
action_id = self.get_message("user:42", 17)
action_id = self.send_message("user:42", "hello", reply_to=17, thread_id=None)
action_id = self.edit_message("user:42", 17, "updated")
action_id = self.download_media("user:42", 17, "0")
action_id = self.send_media("user:42", str(path), kind="document", caption="export")
self.cancel_action(action_id)
```

Text send/edit/media methods accept `entities`, a tuple of dictionaries with
`kind`, `offset`, `length`, and optional `value`. Offsets and lengths use UTF-16;
surrogate pairs cannot be split. Supported kinds are `Bold`, `Italic`, `Underline`,
`Strike`, `Spoiler`, `Code`, `Pre`, and `TextUrl`. `TextUrl` uses `value` for the URL;
`Pre` may use it for a language. Text is limited to 4096 UTF-16 units, media captions
to 1024, and each action to 100 entities. Editing keeps existing attachments.

Successful callbacks return queued actions to native code; inspection, unload,
pre/post-request hooks, and progress callbacks cannot submit actions. Failed
callbacks discard their actions. Plugin-originated message events cannot emit
more actions, although normal text transformations remain available.

Implement `on_action_result(self, result)` and optionally
`on_action_progress(self, progress)`. Both receive dictionaries with `id` and
`status`; results may include `error`, `message`, `messageIDs`, or `path`.
Sending emits `accepted` with local outbox IDs before delivery and `completed`
with confirmed message IDs after Telegram acknowledges it. Other terminal states
are `failed` and `cancelled`. Progress notifications contain `progress` in 0–1 and
are coalesced to at most four per second. Do not treat `accepted` as delivery.
Native failures include `unavailableTarget`, `invalidContent`, `permissionDenied`,
`quotaExceeded`, `timeout`, and `telegramRestriction`. Invalid callback replies or
undeclared action permissions reject the callback and quarantine that plugin's
registrations using the existing error-recovery behavior.

Actions run outside message transactions and registry locks. Limits are 32
outstanding actions and two media transfers per plugin/account, with 30 writes per
minute. Lookup/edit/text-send deadlines are 60 seconds; media operations have ten
minutes and time out after 60 seconds without progress. Telegram flood limits and
other restrictions still apply.

Use `self.data_directory`, a `pathlib.Path`, for generated/downloaded files.
Native uploads accept only regular files within that directory, reject symlinks
and traversal, and take a private snapshot before sending. Each file is limited
to 100 MiB and managed storage to 256 MiB per plugin/account, including snapshots.
Plugins must remove files they no longer need. The directory survives updates and
restarts and is deleted on removal/reset. Interrupted temporary snapshots are
cleaned at registry startup.

Supported upload kinds are `photo`, `video`, and `document`; photos are validated
and converted to JPEG. Downloads reject timed/view-once messages, protected
content and secret chats regardless of retention settings. No media bytes cross
the JSON bridge. Albums, native voice/music rendering and attachment replacement
are outside SDK 1.1.

Disable, safe mode, update, removal, logout and account teardown cancel owned work.
Late completions from retired instances are ignored. Queues are session-only and
are never replayed after restart. Cancellation after outbox handoff is best effort;
it does not retract messages Telegram has already accepted. iOS suspension may
interrupt work; this SDK does not promise background execution.

See [reply.py](examples/plugins/reply.py) and
[send_document.py](examples/plugins/send_document.py). Linux tests validate the
SDK protocol, core executor, generation checks and files. The Telegram adapters,
UIKit, actual transfers, signing and account/device behavior require macOS/iOS
validation with test accounts.
