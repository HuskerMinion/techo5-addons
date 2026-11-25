#!/usr/bin/env python3
"""Download every file catalog.json pins and check it against its pin.

For each version entry that is not withdrawn, each binary, each extra file (the entry's "files", by
the build that gets them) and the manifest (addon.json), when one is pinned, are downloaded and their
SHA-256 and size compared with the entry's. A pinned manifest is then checked by mkcatalog against its
entry (mkcatalog -in CATALOG -manifest FILE), after this script has checked that its id and version are
the entry's and that the extra files it names are the ones the entry pins for every build: mkcatalog
matches a manifest to an entry by the manifest's own id and version, so one naming another would
otherwise pass as having no entry yet.

A version that pins no manifest is checked for its binaries only. Withdrawn versions and add-ons are
skipped: their files may be gone, and nothing of them is installed.

Usage: check-pins.py CATALOG MKCATALOG WORKDIR
"""

import hashlib
import json
import os
import subprocess
import sys
import urllib.request


def fetch(url, size, path):
    """Download url to path, reading at most one byte more than size; return (sha256, bytes read)."""
    h = hashlib.sha256()
    n = 0
    req = urllib.request.Request(url, headers={"User-Agent": "techo5-addons-check"})
    with urllib.request.urlopen(req, timeout=120) as r, open(path, "wb") as f:
        while n <= size:
            chunk = r.read(min(1 << 16, size + 1 - n))
            if not chunk:
                break
            h.update(chunk)
            f.write(chunk)
            n += len(chunk)
    return h.hexdigest(), n


def check(pin, path, what):
    """Download one pinned file and compare it; return a list of problems."""
    try:
        sha, n = fetch(pin["url"], pin["size"], path)
    except Exception as e:  # noqa: BLE001 - every failure is reported the same way
        return [f"{what}: downloading {pin['url']}: {e}"]
    problems = []
    if n != pin["size"]:
        problems.append(f"{what}: {pin['url']} is {n}{'+' if n > pin['size'] else ''} bytes, not {pin['size']}")
    elif sha != pin["sha256"]:
        problems.append(f"{what}: {pin['url']} has sha256 {sha}, not {pin['sha256']}")
    else:
        print(f"ok   {what}: {pin['url']}")
    return problems


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    catalog, mkcatalog, work = sys.argv[1:]
    with open(catalog, encoding="utf-8") as f:
        c = json.load(f)
    os.makedirs(work, exist_ok=True)
    problems = []
    for a in c.get("addons", []):
        if a.get("withdrawn"):
            print(f"skip {a['id']}: withdrawn")
            continue
        for v in a.get("versions", []):
            what = f"{a['id']} {v['version']}"
            if v.get("withdrawn"):
                print(f"skip {what}: withdrawn")
                continue
            for arch, pin in sorted(v.get("binaries", {}).items()):
                path = os.path.join(work, f"{a['id']}-{v['version']}-{arch}")
                problems += check(pin, path, f"{what} {arch}")
            for arch, files in sorted((v.get("files") or {}).items()):
                for i, pin in enumerate(files or []):
                    # Saved under a name of this script's, not the entry's: a name in a pull request
                    # not yet reviewed could be a path out of the work folder.
                    path = os.path.join(work, f"{a['id']}-{v['version']}-{arch}-file{i}")
                    problems += check(pin, path, f"{what} {arch} extra file {pin.get('name')!r}")
            pin = v.get("manifest")
            if not pin:
                print(f"note {what}: pins no manifest, so devices list it without offering to install it")
                continue
            path = os.path.join(work, f"{a['id']}-{v['version']}-addon.json")
            got = check(pin, path, f"{what} addon.json")
            problems += got
            if got:
                continue
            try:
                with open(path, encoding="utf-8") as f:
                    m = json.load(f)
            except ValueError as e:
                problems.append(f"{what} addon.json: not JSON: {e}")
                continue
            if not isinstance(m, dict) or m.get("id") != a["id"] or m.get("version") != v["version"]:
                problems.append(f"{what} addon.json: names {m.get('id') if isinstance(m, dict) else '?'} "
                                f"{m.get('version') if isinstance(m, dict) else '?'}, not its entry")
                continue
            named = sorted(m.get("files") or [], key=str)
            mismatch = False
            for arch in sorted(v.get("binaries", {})):
                pinned = sorted(f.get("name") for f in ((v.get("files") or {}).get(arch) or []))
                if named != pinned:
                    problems.append(f"{what} addon.json: names the extra files {named or 'none'}, and the entry "
                                    f"pins {pinned or 'none'} for {arch}")
                    mismatch = True
            if mismatch:
                continue
            r = subprocess.run([mkcatalog, "-in", catalog, "-manifest", path], capture_output=True, text=True)
            out = (r.stdout + r.stderr).strip()
            if r.returncode != 0:
                problems.append(f"{what} addon.json: {out}")
            else:
                print(f"ok   {what} addon.json: {out}")
    if problems:
        print("\n".join(["", "problems:"] + problems), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
