# TECHO5 add-ons

This repository is the source of [TECHO5](https://github.com/HuskerMinion/techo5)'s add-on catalog,
[`catalog.json`](catalog.json): the list of add-ons that were looked over and can be installed from a
device's setup page.

A device installs only what this catalog lists, and believes the catalog only with its signature. The
maintainer signs it with TECHO5's release key and publishes it on TECHO5's
[`addons` release](https://github.com/HuskerMinion/techo5/releases/tag/addons), which is where devices
fetch it, as two files written from this one (see [Two published files](#two-published-files)). A
change here reaches devices only once it is signed and published; nothing in this repository is
fetched by a device directly.

The catalog is data, not code. The license in [LICENSE](LICENSE) (MIT, as TECHO5's) covers it and the
files here; each add-on has its own license, in its own repository.

## For owners: installing an add-on

Add-ons are installed, updated and removed on the device's setup page, on the **Add-ons** card
(**System** tab). The card lists what the catalog offers for your device, with each add-on's author,
what it does, the ports it needs opened, whether it runs as root, any extra files it downloads beside
its program (by name and size), and roughly how much memory and storage it uses. Every install shows this warning first, and you have to tick the box under it to go
on:

> **Add-ons run on this device with access to its microphones, speaker, network and your Home Assistant
> connection.** They are made and kept by their authors, not by TECHO5. Being listed here means it was
> looked over when it was added. It doesn't mean it's safe, that it will keep working, or that later
> versions were checked. Only install add-ons from people you trust.

Being listed is not a promise that an add-on is safe. It means one version was read and tried before
it was listed, and that the device will run exactly that version's files and open only the ports its
listing shows. How the device runs add-ons (each as a user of its own, only its ports opened, a bounded
log, updates tried before they are kept) is in TECHO5's
[setup guide, Add-ons](https://github.com/HuskerMinion/techo5/blob/main/docs/setup.md#add-ons).

The Echo Show builds (Skylight included), the Echo Spot and the TECHO5 Dot builds run add-ons. TECHO5
Panel doesn't: Android does not let an app run a program it downloaded.

## For authors: getting an add-on listed

Open the
[**Submit an add-on**](https://github.com/HuskerMinion/techo5-addons/issues/new?template=submit-addon.yml)
form on this repository. The maintainer reviews it, and when it is listed, adds an entry for that
version to `catalog.json` by pull request and signs the catalog. Listing is reviewed and may be declined: an add-on has to serve a
real share of TECHO5 owners, and one that is better run by hand (from `rc.local`, as before) may be
pointed there instead.

### What an add-on needs

Checked in review:

- **A public repository with a license.**
- **Releases built and published by CI**, with a `SHA256SUMS` file in each release, and ideally a build
  provenance attestation (for example `actions/attest-build-provenance`), so what is listed is what the
  repository's code builds.
- **One static binary per architecture** (`arm`, `arm64`; at least one of the two) as release assets,
  downloaded over https. They run on TECHO5's own Linux, so they must not need libraries from the
  device.
- **An `addon.json` in each release**, as a release asset beside the binaries (format below).
- **No further executable code downloaded at run time.** The device runs only the files the catalog
  pins by their hashes; an add-on that fetches and runs a plugin, a script or another binary would run
  code nobody looked over. An add-on that needs more than its program (another project's release it
  unpacks, a model) brings it as [extra files](#extra-files), pinned like the binary, and says so in
  the issue; one that needs another role than a program that runs on the device should say so too.
- **No secrets and no telemetry without the owner's say.** Nothing is sent anywhere the owner did not
  set up or agree to, and no keys or accounts are built into the binary.
- **Ports at 1024 or above**, each with a reason, unless it runs as root.
- **Root only with a clear reason**, such as making a network interface for a VPN. The card shows it in
  bold.

Checked by `mkcatalog` and by every device (the definitions are in TECHO5's
[`echod/internal/feature/addons/catalog`](https://github.com/HuskerMinion/techo5/tree/main/echod/internal/feature/addons/catalog)):

- The id is lowercase letters, digits and dashes, starting with a letter, 2 to 40 characters.
- The version is `X.Y.Z` (optionally with a leading `v`, a `-prerelease` and a `_build` part), and
  `addon.json`'s `id` and `version` are exactly its entry's.
- Every download (each binary, each extra file, and `addon.json`) is an https link pinned by its
  SHA-256 and size; a download that doesn't match is refused.
- Each port is `tcp` or `udp`, a single `port` or a `from`/`to` range (not both), with a `why`. None
  may be one of TECHO5's own (tcp 22, 4070, 5000, 6053, 7000, 8181, 8554, 8928, 8940; udp 68, 319-320, 546,
  1900, 3702, 5353, 6001-6010), none may be given twice, and none may be below 1024 unless it runs as
  root.
- `addon.json` asks for exactly the ports and root its catalog entry lists, and names exactly the extra
  files the entry pins for the device's build: a device refuses one that differs, even when its hash
  matches.
- Extra files have plain names (letters, digits, `.`, `-`, `_` and `+`, at most 64, not starting with a
  dot, not ending in `.part`, not the program's name, and neither another's name nor the program's
  followed by a dot, as `x` and `x.gz`), each given once, at most 8 for a build and 128 MB together,
  and every build lists the same names.
- `memory_mb` is more than zero. A device doesn't install or start an add-on that would leave less than
  100 MB of memory for TECHO5.
- JSON is read strictly: keys are lowercase, each key appears once, and a key the format doesn't know
  is refused. `addon.json` is at most 16 KB.
- A version that uses a feature beyond format 1 names it in `requires` (see
  [Format 2 and `requires`](#format-2-and-requires)): one with extra files has `"requires": ["files"]`.

### `addon.json`

techo5-plex's, for example:

```json
{
  "id": "techo5-plex",
  "version": "0.2.0",
  "command": ["techo5-plex"],
  "args": ["-data", "{state}"],
  "ports": [
    {"proto": "tcp", "port": 32500, "why": "Plex apps control the player"},
    {"proto": "tcp", "port": 32501, "why": "its link page"},
    {"proto": "udp", "from": 32410, "to": 32414, "why": "Plex finds players"}
  ],
  "root": false,
  "page": "http://{device}:32501/",
  "memory_mb": 40
}
```

- `id` and `version`: the add-on and this release, as listed.
- `command`: the program's name, then any arguments that come first. The release's binary is installed
  under this name, so it is a plain name, never a path.
- `args`: arguments after the command. `{state}` in one is the add-on's own folder for what it keeps
  (settings, an account it was linked to), which outlives updates.
- `ports`: what it listens on, and why. These are opened on Wi-Fi while it runs, and closed when it
  stops.
- `root`: `true` only if it has to run as root; otherwise it runs as a user of its own.
- `page` (optional): its own web page, which the card links to. `{device}` is the device's address as
  the browser reached it.
- `memory_mb`: roughly how much memory it uses.
- `files` (optional): the names of its [extra files](#extra-files), which its catalog entry pins.

Check a manifest the way a device does, from a TECHO5 checkout's `echod` folder:

```sh
go run ./cmd/mkcatalog -manifest addon.json
```

### Extra files

A program that needs files beside it (another project's release it unpacks, a model) names them in
`addon.json`, `"files": ["netbird.tar.gz"]`, and its catalog entry pins each one as it pins the binary.
The device downloads and checks each one as it does the program, and refuses the whole install or
update if one doesn't match. They are installed read-only (root's, `0644`) in the add-on's `bin`
folder beside the program, under those names; the program finds that folder in `TECHO5_ADDON_BIN`
(and its `state` folder in `TECHO5_ADDON_STATE`). An update replaces them with the program, going back
to the version before puts the old ones back, and removing the add-on deletes them. An update that
adds a file or changes one asks the owner again, as one asking for a new port does.

They are keyed by the TECHO5 build that gets them, `arm` or `arm64` as the binaries are, whatever is
inside them: NetBird's add-on pins its own `arm` build and, under `arm`, NetBird's `linux_arm64`
archive, since every device it runs on has a 64-bit kernel. One `addon.json` serves every build, so
each build lists the same names. In the entry:

```json
"requires": ["files"],
"binaries": {
  "arm": {"url": "https://github.com/example/techo5-netbird/releases/download/v0.2.0/techo5-netbird-arm", "sha256": "…", "size": 9000000}
},
"files": {
  "arm": [
    {"name": "netbird.tar.gz", "url": "https://github.com/netbirdio/netbird/releases/download/vX.Y.Z/netbird_X.Y.Z_linux_arm64.tar.gz", "sha256": "…", "size": 15000000}
  ]
}
```

An add-on that unpacks one is welcome to check its SHA-256 again against its own pin before it does;
it never downloads it itself when it runs from the catalog.

### Format 2 and `requires`

`catalog.json` here is format 2 (`"format": 2`). A version can carry `requires`, the features it needs
that a device has to know to install it:

```json
{
  "version": "0.2.0",
  "requires": ["files"],
  "min_techo5": {"show": "v1.6.52"},
  "binaries": {"arm": {"url": "…", "sha256": "…", "size": 9000000}},
  "files": {"arm": [{"name": "netbird.tar.gz", "url": "…", "sha256": "…", "size": 15000000}]},
  "ports": [],
  "root": true,
  "memory_mb": 40,
  "disk_mb": 30
}
```

The only feature today is `files`, the [extra files](#extra-files). A version that uses one names it,
and a version names only what it uses; `mkcatalog` refuses either way round.

This is how the catalog grows without breaking devices. A device skips a version that requires a
feature it doesn't know, rather than refusing the whole catalog over a field it can't read; an add-on
with no version it can read is shown grayed out, as needing a newer TECHO5. Nothing else is loosened:
a key the format doesn't know is still refused everywhere else, and a device that knows a feature reads
its fields as strictly as the rest. So a new field comes with a new feature name, and every version that
uses it requires it.

### Two published files

Devices up to TECHO5 v1.6.53 read only format 1, strictly: one field they don't know (such as
`files`) and they refuse the whole catalog, listing nothing. So `mkcatalog` writes two files from this
one, each signed under its own domain so neither's signature verifies as the other:

- `catalog-v2.json`: everything, in format 2. Newer devices fetch it first.
- `catalog.json`: format 1, exactly as older devices read it, with every version that requires
  anything left out, and an add-on with no version left left out too. Older devices go on listing what
  they can install; newer devices fall back to it only while `catalog-v2.json` isn't published.

Both carry the same serial and expiry. A version once in `catalog.json` can't come to require
something later: that would take it away from the devices that installed it.

### What the catalog entry adds

The maintainer writes the entry from the release; you don't need to. Besides what `addon.json` says,
it gives the oldest TECHO5 version for each family it runs on (`min_techo5`: `show`, `spot`, `dot`),
optionally the boards it is limited to, and roughly how much storage it uses (`disk_mb`; what it keeps
in its `state` folder is held to four times that, at least 64 MB). The pins are measured from the
downloaded files with `mkcatalog -pin URL=FILE` (with `-file NAME` for an extra file, which prints it
under its name), never typed by hand. A version whose release has no
`addon.json` can be listed, but devices show it without offering to install it.

### How a submission is reviewed

The maintainer, before listing a version:

- reads the code for what it does on the device: what it runs, what it reads, and what it changes;
- checks what it reaches over the network, and what it sends there;
- checks what it stores, where, and how much;
- checks how it updates: only by a new release listed here, never by fetching code itself;
- checks the license;
- builds or downloads the release, checks it against its `SHA256SUMS` (and attestation, if any), and
  tries it on a device.

### Once listed

- **A listed version never changes.** A new release is a new version entry, reviewed on its own: a
  version is never trusted because an earlier one was. The signing tool refuses a catalog that changes
  or drops a published version. The add-on's author can't change either; its name, summary and links
  can be corrected.
- **Withdrawal.** A version, or a whole add-on, that has to come out stays in the catalog marked
  withdrawn, with the reason. Devices that have it say it is no longer listed and suggest removing it;
  they don't remove it themselves, and nothing of it is installed from then on. A withdrawn add-on is
  not listed again under the same entry.
- **The signed catalog expires** a month after it is signed, and every TECHO5 release signs it again.
  Past that, installed add-ons keep running, but nothing new is offered. A device never goes back to an
  older catalog than one it has seen.

Firmware bugs go to [TECHO5's issues](https://github.com/HuskerMinion/techo5/issues), problems with an
add-on itself to its own repository.

## For the maintainer

Each push and pull request runs [check.yml](.github/workflows/check.yml): it builds `mkcatalog` from
TECHO5's `main`, checks `catalog.json` the way a device reads it, in both formats it is published as,
downloads every pinned file (binaries, extra files and manifests) and checks its SHA-256 and size, and
checks each pinned `addon.json` against its entry, its extra files' names among it. A catalog that uses
a field or requires a feature TECHO5's `main` doesn't know yet fails there; `tools/check-pins.py`
likewise fails on a feature whose downloads it hasn't been taught to check. A device too old to know a
feature skips the versions that require it, and a format 1 device never sees them.

To publish, run TECHO5's `tools/sign-catalog.ps1`, which publishes all four files (`catalog-v2.json`,
`catalog.json` and their `.sig` files), on the computer that holds the release key, with this
repository checked out beside TECHO5's (or named by `-Catalog` or `$env:TECHO5_ADDONS`). It signs only
a catalog that is committed and at `origin/main` here, with `mkcatalog` built from a clean TECHO5 at
its `origin/main`; raise `serial` with every change. `tools/release.ps1` runs it with every release. The
first signing that publishes `catalog-v2.json` passes `-FirstFormat2`; every one after it is checked
against the published `catalog-v2.json` as well as `catalog.json`, and refused without it.
