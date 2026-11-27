#!/usr/bin/env python3
"""Build a static Kodi add-on repository using only the Python standard library."""

from __future__ import annotations

import hashlib
import html
import io
import sys
import zipfile
from pathlib import Path, PurePosixPath
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://tom-lei.github.io/kodi-repo/"
REPOSITORY_ID = "repository.tom-lei"
REPOSITORY_VERSION = "2026.11.27"
REPOSITORY_DIR = ROOT / REPOSITORY_ID
PACKAGE_DIR = ROOT / "packages"


def parse_addon(xml_bytes: bytes, source: str) -> tuple[str, str, str]:
    try:
        addon = ElementTree.fromstring(xml_bytes)
    except ElementTree.ParseError as exc:
        raise ValueError(f"{source}: invalid addon.xml: {exc}") from exc
    if addon.tag != "addon":
        raise ValueError(f"{source}: addon.xml root must be <addon>")
    addon_id = addon.get("id", "")
    version = addon.get("version", "")
    name = addon.get("name", addon_id)
    if not addon_id or not version or not name:
        raise ValueError(f"{source}: addon.xml must define id, version, and name")
    return addon_id, version, name


def make_repository_zip() -> bytes:
    filenames = ("addon.xml", "LICENSE", "README.md", "changelog.txt")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for filename in filenames:
            contents = (REPOSITORY_DIR / filename).read_bytes().replace(b"\r\n", b"\n")
            entry = zipfile.ZipInfo(f"{REPOSITORY_ID}/{filename}", date_time=(2020, 1, 1, 0, 0, 0))
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, contents)
    return buffer.getvalue()


def read_release_package(path: Path) -> tuple[str, str, bytes, bytes]:
    package_bytes = path.read_bytes()
    try:
        with zipfile.ZipFile(io.BytesIO(package_bytes)) as archive:
            names = [name for name in archive.namelist() if not name.endswith("/")]
            if not names:
                raise ValueError(f"{path.name}: package ZIP is empty")
            top_levels = set()
            for name in names:
                item = PurePosixPath(name)
                if item.is_absolute() or ".." in item.parts or not item.parts:
                    raise ValueError(f"{path.name}: unsafe ZIP path {name!r}")
                top_levels.add(item.parts[0])
            if len(top_levels) != 1:
                raise ValueError(f"{path.name}: files must have one add-on-ID top-level directory")
            addon_id = top_levels.pop()
            addon_xml_path = f"{addon_id}/addon.xml"
            if addon_xml_path not in names:
                raise ValueError(f"{path.name}: missing {addon_xml_path}")
            xml_bytes = archive.read(addon_xml_path)
    except zipfile.BadZipFile as exc:
        raise ValueError(f"{path.name}: invalid ZIP archive") from exc
    parsed_id, version, _ = parse_addon(xml_bytes, path.name)
    if parsed_id != addon_id:
        raise ValueError(f"{path.name}: top-level directory {addon_id!r} does not match add-on ID {parsed_id!r}")
    return addon_id, version, package_bytes, xml_bytes


def write_bytes(path: Path, contents: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(contents)


def write_package_artwork(output: Path, addon_id: str, package: bytes, addon_xml: bytes) -> None:
    assets = ElementTree.fromstring(addon_xml).find("./extension[@point='xbmc.addon.metadata']/assets")
    if assets is None:
        return
    with zipfile.ZipFile(io.BytesIO(package)) as archive:
        for asset in assets:
            if not asset.text:
                continue
            name = asset.text.strip()
            path = PurePosixPath(name)
            if path.is_absolute() or not path.parts or ".." in path.parts or "\\" in name:
                raise ValueError(f"{addon_id}: invalid artwork path {name!r}")
            archive_path = f"{addon_id}/{path.as_posix()}"
            try:
                data = archive.read(archive_path)
            except KeyError as exc:
                raise ValueError(f"{addon_id}: missing artwork {archive_path}") from exc
            write_bytes(output / addon_id / Path(*path.parts), data)


def build(output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    packages: dict[tuple[str, str], tuple[bytes, bytes]] = {}

    repository_xml = (REPOSITORY_DIR / "addon.xml").read_bytes()
    repository_id, repository_version, _ = parse_addon(repository_xml, "repository add-on")
    if (repository_id, repository_version) != (REPOSITORY_ID, REPOSITORY_VERSION):
        raise ValueError("repository add-on ID/version must match the configured release")
    packages[(repository_id, repository_version)] = (make_repository_zip(), repository_xml)

    if PACKAGE_DIR.exists():
        for path in sorted(PACKAGE_DIR.glob("*.zip")):
            addon_id, version, package_bytes, addon_xml = read_release_package(path)
            key = (addon_id, version)
            if key in packages:
                raise ValueError(f"duplicate package {addon_id} {version}")
            packages[key] = (package_bytes, addon_xml)

    addons = ElementTree.Element("addons")
    for (addon_id, version), (package_bytes, addon_xml) in sorted(packages.items()):
        parsed_id, parsed_version, _ = parse_addon(addon_xml, f"{addon_id} {version}")
        if (parsed_id, parsed_version) != (addon_id, version):
            raise ValueError(f"package metadata mismatch for {addon_id} {version}")
        addon_element = ElementTree.fromstring(addon_xml)
        addons.append(addon_element)
        filename = f"{addon_id}-{version}.zip"
        relative = Path(addon_id) / filename
        write_bytes(output / relative, package_bytes)
        write_package_artwork(output, addon_id, package_bytes, addon_xml)
        write_bytes(
            output / f"{relative}.sha256",
            (hashlib.sha256(package_bytes).hexdigest() + "\n").encode("ascii"),
        )

    xml_bytes = ElementTree.tostring(addons, encoding="utf-8", xml_declaration=True)
    write_bytes(output / "addons.xml", xml_bytes)
    write_bytes(
        output / "addons.xml.sha256",
        (hashlib.sha256(xml_bytes).hexdigest() + "\n").encode("ascii"),
    )
    write_bytes(output / "index.html", make_index(packages))


def make_index(packages: dict[tuple[str, str], tuple[bytes, bytes]]) -> bytes:
    links = []
    for (addon_id, version), _ in sorted(packages.items()):
        label = "Install repository" if addon_id == REPOSITORY_ID else f"Download {addon_id} {version}"
        href = f"{html.escape(addon_id)}/{html.escape(addon_id)}-{html.escape(version)}.zip"
        links.append(f'<li><a href="{href}">{html.escape(label)} ({html.escape(version)})</a></li>')
    package_list = "\n".join(links)
    document = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>kodi-repo</title>
</head>
<body>
  <main>
    <h1>kodi-repo</h1>
    <p>Private archive only. The configured repository feed is offline; install add-on ZIPs manually.</p>
    <p><a href="{REPOSITORY_ID}/{REPOSITORY_ID}-{REPOSITORY_VERSION}.zip">repository.tom-lei-{REPOSITORY_VERSION}.zip</a></p>
    <p>Catalogue:</p>
    <ul>{package_list}</ul>
    <p>See <a href="https://github.com/tom-lei/kodi-repo">installation and release notes</a>.</p>
  </main>
</body>
</html>
"""
    return document.encode("utf-8")


def main() -> int:
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "site"
    try:
        build(output.resolve())
    except (OSError, ValueError) as exc:
        print(f"Repository build failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
