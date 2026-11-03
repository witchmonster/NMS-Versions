"""Refresh the public Windows EXE-label index from official GOG metadata.

The developer-label suffix interpretation is an approved NMS-specific rule,
not a claim that GOG and Steam binaries or decoder compatibility are equal.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
SOURCE = "https://content-system.gog.com/products/1446213994/os/windows/builds?generation=2"
NAMESPACE = "nms.gog.windows.exe"
MAX_BYTES = 2 * 1024 * 1024
LABEL = re.compile(r"(\d+\.\d+)_([^_]+)_([1-9]\d{0,19})")
IDENTIFIER = re.compile(r"[1-9]\d{0,19}")


def version(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d+\.\d+", value):
        raise ValueError("Invalid public version")
    return tuple(map(int, value.split(".")))


def publication(value):
    if not isinstance(value, str):
        raise ValueError("GOG publication timestamp must be a string")
    date = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if date.tzinfo is None:
        raise ValueError("GOG publication timestamp needs an explicit timezone")
    return date.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def family(value):
    if not isinstance(value, str) or not value or value != value.strip() or len(value) > 80 or any(ord(c) < 32 for c in value):
        raise ValueError("Invalid named update family")
    return value


def notes_url(value):
    if not isinstance(value, str):
        raise ValueError("Invalid official notes URL")
    url = urlsplit(value)
    if url.scheme != "https" or url.netloc != "www.nomanssky.com" or url.query or url.fragment or not url.path.startswith("/"):
        raise ValueError("Notes must name an official Hello Games page")
    return value


def decode(raw):
    if len(raw) > MAX_BYTES:
        raise ValueError("Index/source exceeds its size limit")
    return json.loads(raw.decode("utf-8-sig"))


def validate(index):
    if not isinstance(index, dict) or set(index) != {"schemaVersion", "namespace", "builds"} or type(index["schemaVersion"]) is not int or index["schemaVersion"] != 2 or index["namespace"] != NAMESPACE:
        raise ValueError("Expected the GOG Windows EXE index namespace/schema")
    if not isinstance(index["builds"], list) or not index["builds"]:
        raise ValueError("A functional index needs build mappings")
    result = {}
    required = {"executableBuild", "version", "family", "gogPublishedAt"}
    for row in index["builds"]:
        if not isinstance(row, dict) or not required <= set(row) or set(row) - required - {"notesUrl"}:
            raise ValueError("Unexpected build fields")
        key = row["executableBuild"]
        if not isinstance(key, str) or not IDENTIFIER.fullmatch(key) or key in result:
            raise ValueError("Invalid or duplicate full EXE build")
        if version(row["version"]) < (7, 10):
            raise ValueError("Index contains a version before 7.10")
        family(row["family"])
        if publication(row["gogPublishedAt"]) != row["gogPublishedAt"]:
            raise ValueError("Public timestamps must use UTC ISO 8601")
        if "notesUrl" in row:
            notes_url(row["notesUrl"])
        result[key] = dict(row)
    return result


def previous(raw):
    """Read accepted history, or migrate the former notes-only catalogue.

    A catalogue contributes notes links only. It never supplies EXE mappings,
    console entries, RSS-as-GOG dates or Steam identities to the new index.
    """
    if raw is None:
        return {}, {}
    index = decode(raw)
    if not isinstance(index, dict):
        raise ValueError("Unrecognized history; preserve it for the owner")
    if index.get("schemaVersion") == 2:
        rows = validate(index)
        notes = {}
        for row in rows.values():
            if "notesUrl" in row:
                key = (row["version"], row["family"])
                if key in notes and notes[key] != row["notesUrl"]:
                    raise ValueError("Conflicting retained official notes links")
                notes[key] = row["notesUrl"]
        return rows, notes
    if set(index) != {"schemaVersion", "releases"} or type(index["schemaVersion"]) is not int or index["schemaVersion"] != 1 or not isinstance(index["releases"], list):
        raise ValueError("Unrecognized history; preserve it for the owner")
    notes = {}
    for row in index["releases"]:
        if not isinstance(row, dict) or set(row) != {"version", "family", "platforms", "notesUrl", "rssPublishedAt"}:
            raise ValueError("Unrecognized legacy catalogue row")
        version(row["version"])
        family(row["family"])
        publication(row["rssPublishedAt"])
        key = (row["version"], row["family"])
        if key in notes or not isinstance(row["platforms"], list) or not all(isinstance(p, str) for p in row["platforms"]):
            raise ValueError("Invalid or duplicate legacy catalogue row")
        notes[key] = notes_url(row["notesUrl"])
    return {}, notes


def produce(raw, history=None):
    source = decode(raw)
    if not isinstance(source, dict) or not isinstance(source.get("items"), list) or type(source.get("count")) is not int or type(source.get("total_count")) is not int or source["count"] != len(source["items"]) or not 0 < source["count"] <= source["total_count"]:
        raise ValueError("Malformed or empty GOG build response")
    retained, notes = previous(history)
    found = {}
    for item in source["items"]:
        fields = {"product_id", "public", "os", "branch", "generation", "build_id", "version_name", "date_published"}
        if not isinstance(item, dict) or not fields <= set(item) or item["product_id"] != "1446213994":
            raise ValueError("GOG product namespace mismatch")
        if type(item["public"]) is not bool or not isinstance(item["os"], str) or (item["branch"] is not None and not isinstance(item["branch"], str)):
            raise ValueError("Malformed GOG platform/public/branch metadata")
        if item.get("public") is not True or item.get("os") != "windows" or item.get("branch") is not None:
            continue
        if item.get("generation") != 2 or not isinstance(item.get("build_id"), str) or not IDENTIFIER.fullmatch(item["build_id"]):
            raise ValueError("Malformed GOG generation/build identity")
        label = item.get("version_name")
        match = LABEL.fullmatch(label) if isinstance(label, str) else None
        if not match:
            raise ValueError("Malformed public Windows developer label")
        patch, update, exe = match.groups()
        family(update)
        published = publication(item.get("date_published"))
        if version(patch) < (7, 10):
            continue
        row = {"executableBuild": exe, "version": patch, "family": update, "gogPublishedAt": published}
        if (patch, update) in notes:
            row["notesUrl"] = notes[(patch, update)]
        if exe in found and found[exe] != row:
            raise ValueError("Conflicting GOG labels/publication records for one EXE build")
        found[exe] = row
    if not found:
        raise ValueError("No public Windows mappings in the source response")
    for key, row in found.items():
        if key in retained and retained[key] != row:
            raise ValueError("Source conflicts with retained historical mapping")
        retained[key] = row
    result = {"schemaVersion": 2, "namespace": NAMESPACE,
              "builds": [retained[key] for key in sorted(retained, key=int)]}
    validate(result)
    return result


def lookup(index, executable_build):
    rows = validate(index)
    if not isinstance(executable_build, str) or not IDENTIFIER.fullmatch(executable_build):
        return None
    return rows.get(executable_build)


def fetch():
    request = Request(SOURCE, headers={"User-Agent": "NMS-Versions/2"})
    with urlopen(request, timeout=30) as response:
        if response.url != SOURCE:
            raise ValueError("GOG source redirected; preserve the last good index")
        raw = response.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("GOG response exceeds its size limit")
    return raw


def read(path):
    if path.is_symlink() or path.is_junction():
        raise ValueError("Refuse a linked index/history path")
    return path.read_bytes() if path.exists() else None


def refresh(output, history=None, source_file=None):
    output = Path(output).absolute()
    for parent in [output.parent, *output.parents]:
        if parent.is_symlink() or parent.is_junction():
            raise ValueError("Refuse a linked output directory")
    before = read(output)
    history = Path(history).absolute() if history else output
    old = read(history)
    raw = Path(source_file).read_bytes() if source_file else fetch()
    index = produce(raw, old)
    content = (json.dumps(index, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    # Preserve exact bytes and avoid daily commits when facts/order do not change.
    if before is not None and decode(before) == index:
        if read(output) != before or read(history) != old:
            raise ValueError("Index/history changed concurrently; preserve the owner's edit")
        return False, index
    work = ROOT / "target" / "refresh"
    if any(p.is_symlink() or p.is_junction() for p in [work, *work.parents]):
        raise ValueError("Refuse linked temporary staging")
    work.mkdir(parents=True, exist_ok=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.drive.lower() != work.drive.lower():
        raise ValueError("Atomic staging must share the output volume")
    with tempfile.NamedTemporaryFile(dir=work, prefix="index-", suffix=".tmp", delete=False) as stage:
        stage.write(content)
        stage.flush()
        os.fsync(stage.fileno())
        staged = Path(stage.name)
    if read(output) != before or read(history) != old:
        raise ValueError("Index/history changed concurrently; preserve the owner's edit")
    os.replace(staged, output)
    return True, index


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--history", type=Path, help="Read accepted prior history/legacy notes without changing it")
    parser.add_argument("--source-file", type=Path, help="Replay captured official GOG response; no network request")
    args = parser.parse_args()
    changed, index = refresh(args.output, args.history, args.source_file)
    print(json.dumps({"changed": changed, "buildCount": len(index["builds"])}))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, TypeError, KeyError) as error:
        print(f"Refresh refused; last good index preserved: {error}", file=sys.stderr)
        sys.exit(1)
