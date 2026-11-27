# kodi-repo

This private repository stores versioned Kodi add-on ZIPs for personal use.
GitHub Pages is disabled. The generated catalogue and repository add-on still
point to the former Pages URL, which is not an available update feed. Installing
the repository add-on does not provide automatic updates while it is offline.

## Install

While signed in to GitHub with access to this private repository, download an
add-on's versioned ZIP from `packages/`, transfer it to the Kodi device, and
use **Install from zip file**. Kodi may need its official repository enabled
to resolve add-on dependencies. The repository add-on ZIPs are in
`site/repository.tom-lei/` but their configured feed is unavailable.

## DDNS Proxyᵀ 2026.11.27.1 notes

- Offers authenticated proxy access, DDNS providers, port mapping, diagnostics,
  optional shared-port mode, bandwidth statistics and certificate guidance.
- Outbound Kodi HTTPS proxy settings are unsupported and fail closed.
  LibreELEC hardware/shared-port mode and Android have not been tested.
  Manual alternate-port mappings require clients to adjust their port.
- 3proxy and Linux PCRE2 are downloaded at runtime with verification; see the
  included third-party notices and service disclosures.

## simpliTVᵀ 2026.11.27 notes

- Improves channel switching, guide navigation, channel number input and
  playback handoff; routes add-on HTTP requests through Kodi's configured proxy.
- Checks Widevine with InputStream Helper and uses the device's local timezone.
- 230 offline tests passed, with one skipped; this exact ZIP was not tested
  in Kodi. See the included changelog for details.

## simpliTVᵀ 2026.11.23.3 notes

- Includes guide-background and recovery-menu fixes, plus programme-jump
  handling for queued seeks, repeated taps, and near-boundary landings.
- 141 offline tests passed. A synthetic retry and one real-provider retry
  exercised two rapid Previous and Next commands while the first seek was
  pending, advancing twice in both directions. Provider requests and player
  readbacks completed within 2.8 seconds. These inputs used direct `onAction`
  calls with injected context-menu choices, not physical remote/Kodi input
  dispatch. EPG data and player readbacks were real; broadcast wall-clock
  alignment was not independently measured. Near-boundary and tap-reversal
  fixes were offline-tested only.
- An earlier enlarged-preview session on Windows exited with an unexplained
  crash (`0xC0000005`); its cause remains unknown.
- Unencrypted streams, Android, and LibreELEC remain untested.
- simpliTVᵀ is unofficial and based on the simpliTV add-on by Publish3r and
  sunsettrack4. Its source, license and credits are included in the release ZIP.
  The T-branded icon and fanart are derivatives of artwork included in the
  [upstream GPLv3-or-later package](https://github.com/Publish3r/repository.kodi.matrix/tree/8a2e0597051d582f0dcb4df8ce8a66961725f964/plugin.video.simplitv).
  No artwork exclusion was identified there; rights to third-party branding
  and trademarks remain unverified. No affiliation or endorsement is implied.

## Publishing a separately released add-on

Only add a reviewed, versioned release ZIP to `packages/`. The ZIP must contain
the add-on in its ID-named top-level directory, including its `addon.xml`; do not
add working source trees or development artifacts. Run
`python tools/build_repository.py` and review the generated catalogue, package,
and hashes before committing to the private repository. The Pages workflow is
preserved but disabled: it has no push trigger and its build job is gated off,
so it neither deploys nor uploads contents. Keep each released versioned ZIP in the
repository. Add-on source, licensing, and release obligations remain with each
add-on and are not changed by this repository's license.

## Development

Build the static site with the Python standard library:

```powershell
python tools/build_repository.py
python -m unittest discover -s tests
```

The generator creates `site/`, including `addons.xml`, its SHA-256 checksum,
versioned add-on packages, and `.sha256` package sidecars. Kodi uses a
`Content-Sha256` HTTP header when available and falls back to
`<package>.sha256`; the sidecars are included for a compatible future host.

The repository add-on uses `YYYY.MM.DD[.N]` versions; its release history is in
[changelog.txt](repository.tom-lei/changelog.txt). The earlier 1.0.0 installer
remains available for existing links.

## License

The original repository scaffold and build scripts are licensed under
GPL-3.0-or-later; see [LICENSE](LICENSE). This does not relicense any separately
published add-on.
