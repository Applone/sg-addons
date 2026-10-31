# Swiftgram Python plugins, SDK 1.0

Swiftgram embeds CPython and a small native-facing Python SDK. Plugins are real
Python source files, with functions, classes, loops, and supported standard-library
imports. Install `.py` or `.plugin` files from **Additional functions → Plugins**.
Only Python source files are accepted. See the [complete example](examples/plugins/uppercase.py).

## Dependencies

The IPA supplies the pinned CPython runtime, its platform-supported standard
library, and the Swiftgram SDK needed to interact with the application.
**Third-party dependencies are unsupported. There is no dependency resolution,
package download, installation, wheel import, or package registry.**

Python declarations `__requirements__`, `__dependencies__`, `requirements`, and
`dependencies` are rejected, even when empty. Inline script dependency metadata is
also rejected. These checks happen before plugin execution and again when
restoring a source for execution. A missing import raises `ModuleNotFoundError`;
it never triggers a lookup or installation.

The runtime does not discover user/system site packages or read Python environment
variables. The packaged library excludes `ensurepip`, `venv`, wheel archives, and
`site-packages`. The application adds only its bundled SDK to the interpreter's
standard library paths. The CPython framework is fetched by the build from a pinned,
SHA-256-verified archive; this is an application build dependency, not an on-device
plugin package manager. Bundled native standard-library modules are packaged as
frameworks for normal application signing.

This is a support boundary, not a Python security sandbox. Trusted plugin code runs
inside the application process, can use available filesystem/network APIs, and can
modify Python process state. SDK permissions control the host callbacks exposed to
plugins; they do not isolate arbitrary Python execution or shared standard-library
modules. No claim of safe third-party dependency isolation is made. Adding package
support would require a separate architecture and security review, rather than a
shared import directory with ownership counters.

## Python file contract

Metadata is read from literal top-level assignments using the bundled AST parser;
inspection does not import or execute the plugin. Files must be UTF-8 and at most
256 KB. IDs use 2–32 ASCII characters: a letter first, followed by letters, digits,
`_`, or `-`. Names must be nonblank and at most 120 UTF-8 bytes. Versions have
1–4 numeric components, each from 0 to 999999. Optional SDK/app constraints use
`>=`, `<=`, `==`, `>`, or `<` followed by a numeric version; missing components
compare as zero. SDK version is `1.0`. Author and description limits are 120 and
2048 UTF-8 bytes. At most 64 plugins and 32 MB of registry data are allowed.

```python
__id__ = "uppercase"
__name__ = "Uppercase messages"
__version__ = "1.0"
__permissions__ = ["outgoingMessages"]
__hooks__ = [{"event": "sendMessage", "name": "send_message"}]

from swiftgram import BasePlugin, HookResult, HookStrategy

class Plugin(BasePlugin):
    def on_send_message(self, event):
        return HookResult(HookStrategy.MODIFY, text=event.text.upper())
```

`__id__` and `__name__` are required. Optional declarations are `__version__`
(default `1.0`), `__author__`, `__description__`, `__sdk_version__`,
`__app_version__`, `__permissions__`, `__hooks__`, `__settings__`, and `__menus__`.
Arrays default to empty, with at most 32 hooks, 32 settings, and 16 menus per
plugin. Each hook declares `event`, `name`, and optional `substring`, `priority`,
and `callback`. Event names are case sensitive; matching is exact unless
`substring` is `True`. Priorities range from -1000 to 1000. Plugins run in descending
matching priority, with IDs breaking ties in ascending order. Each plugin runs
once, using its highest matching hook, then declaration order. Filtering,
conditions, text construction, and result strategies belong in Python callbacks.
A callback name must be an ASCII Python identifier, at most 64 bytes.

| Permission | SDK access |
| --- | --- |
| `incomingMessages` | Read, change, or suppress locally displayed cloud-message text; read message menu context |
| `outgoingMessages` | Change or cancel composed cloud-message text and media captions |
| `network` | Cancel named requests and change existing terminal error descriptions |
| `menus` | Add native copy and information actions |

Permissions may not repeat. Hooks require the corresponding permission; message
menus require both `menus` and `incomingMessages`.

Define `class Plugin(BasePlugin)`. Each enabled account receives its own instance
and source-module namespace. `self.account` is the host account ID and
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

Import a `.py` or `.plugin` source file through Files, review its permissions and
code-trust notice, then install it. Installation is app-wide; new plugins start
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

CPython runs on a serial native worker with GIL coordination. The host waits at
most 250 ms for hook/menu calls and two seconds for inspection/lifecycle work.
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

Python SDK tests cover non-executing metadata inspection, rejected dependency
metadata, restored-source validation, ordinary Python/standard-library behavior,
missing imports, lifecycle, exceptions, and cooperative deadlines. Native core
checks exercise the C/Swift/CPython boundary, settings, menus, rollback, and explicit
missing-dependency failure. Run `just test` after source preparation, or
`just test-python` for the Python SDK checks alone. Both `test-python` and
`test-core` accept an optional prepared source directory. Native checks
need Swift, Clang, and Python 3.12+ with development headers and a shared library.

The iOS framework, UIKit, signing, and device lifecycle still require macOS/iOS
verification; Linux checks do not establish those properties.
