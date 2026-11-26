"""Generate AltStore source metadata from the two unsigned release IPAs."""

import argparse
import json
import plistlib
import re
import shutil
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from zipfile import ZipFile


def permissions(archive: ZipFile) -> dict[str, object]:
    entitlements: set[str] = set()
    privacy: dict[str, str] = {}
    with tempfile.TemporaryDirectory() as directory:
        executable = Path(directory) / "executable"
        for name in archive.namelist():
            if not name.endswith((".app/Info.plist", ".appex/Info.plist")):
                continue
            info = plistlib.loads(archive.read(name))
            privacy.update({k: v for k, v in info.items() if "UsageDescription" in k})
            member = Path(name).with_name(info["CFBundleExecutable"])
            with archive.open(str(member)) as source, executable.open("wb") as target:
                shutil.copyfileobj(source, target)
            result = subprocess.run(
                ["codesign", "-d", "--entitlements", ":-", executable],
                capture_output=True,
                env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"},
            )
            if result.returncode and b"code object is not signed at all" not in result.stderr:
                result.check_returncode()
            if result.stdout:
                entitlements.update(plistlib.loads(result.stdout))
    return {"entitlements": sorted(entitlements), "privacy": privacy}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifacts", type=Path)
    parser.add_argument("repository")
    parser.add_argument("tag")
    args = parser.parse_args()
    revision = json.loads(Path("upstream.json").read_text())["revision"]
    icon = (
        f"https://raw.githubusercontent.com/Swiftgram/Telegram-iOS/{revision}/Telegram/"
        "Telegram-iOS/DefaultAppIcon.xcassets/AppIconLLC.appiconset/Swiftgram.png"
    )
    date = datetime.now(UTC).isoformat()
    apps = []
    for edition in ("lite", "full"):
        ipa = args.artifacts / f"Swiftgram-{edition}.ipa"
        with ZipFile(ipa) as archive:
            (plist,) = [
                n for n in archive.namelist() if re.fullmatch(r"Payload/[^/]+\.app/Info.plist", n)
            ]
            info = plistlib.loads(archive.read(plist))
            app_permissions = permissions(archive)
            for bundle in ("SwiftgramPython.bundle", "SwiftgramPythonSDK.bundle"):
                present = any(bundle in name.split("/") for name in archive.namelist())
                if present != (edition == "full"):
                    raise ValueError(f"{ipa.name} has unexpected packaging for {bundle}")
        apps.append(
            {
                "name": f"Swiftgram {edition.title()}",
                "bundleIdentifier": info["CFBundleIdentifier"],
                "developerName": "sg-addons",
                "localizedDescription": (
                    "Swiftgram with native add-ons."
                    if edition == "lite"
                    else "Swiftgram with native add-ons, HTML message widgets and Python plugins."
                ),
                "iconURL": icon,
                "appPermissions": app_permissions,
                "versions": [
                    {
                        "version": info["CFBundleShortVersionString"],
                        "buildVersion": info["CFBundleVersion"],
                        "date": date,
                        "minOSVersion": info["MinimumOSVersion"],
                        "downloadURL": f"https://github.com/{args.repository}/releases/download/{args.tag}/{ipa.name}",
                        "size": ipa.stat().st_size,
                    }
                ],
            }
        )
    if apps[0]["bundleIdentifier"] == apps[1]["bundleIdentifier"]:
        raise ValueError("Lite and Full must have distinct bundle identifiers")
    source = {
        "name": "Swiftgram Add-ons",
        "identifier": args.repository.replace("/", "."),
        "apps": apps,
        "news": [],
    }
    (args.artifacts / "altsource.json").write_text(json.dumps(source, indent=2) + "\n")


if __name__ == "__main__":
    main()
