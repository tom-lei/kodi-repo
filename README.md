# kodi-repo

Kodi add-on repository at <https://tom-lei.github.io/kodi-repo/>.

## Install

Download the repository add-on ZIP:

<https://tom-lei.github.io/kodi-repo/repository.tom-lei/repository.tom-lei-1.0.0.zip>

In Kodi, install that downloaded ZIP using **Install from zip file**, then
choose **Install from repository → kodi-repo → Video add-ons → simpliTVᵀ**.
The [download page](https://tom-lei.github.io/kodi-repo/) also links to the
[simpliTVᵀ 2026.11.22 ZIP](https://tom-lei.github.io/kodi-repo/plugin.video.simplitv_t/plugin.video.simplitv_t-2026.11.22.zip).

## simpliTVᵀ 2026.11.22 notes

- One enlarged-preview session on Windows exited with an unexplained crash
  (`0xC0000005`); subsequent runs did not establish its cause or crash safety.
- Unencrypted streams, Android, and LibreELEC have not been tested.
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
and hashes before publishing. The Pages workflow builds and deploys the static
site from `main`. Keep each released versioned ZIP in the repository so existing
Kodi installations can continue to download it. Add-on source, licensing, and
release obligations remain with each add-on and are not changed by this
repository's license.

## Development

Build the static site with the Python standard library:

```powershell
python tools/build_repository.py
python -m unittest discover -s tests
```

The generator creates `site/`, including `addons.xml`, its SHA-256 checksum,
versioned add-on packages, and `.sha256` package sidecars. Kodi uses a
`Content-Sha256` HTTP header when available and falls back to
`<package>.sha256`; GitHub Pages does not provide custom hash headers, so these
sidecars are included.

## License

The original repository scaffold and build scripts are licensed under
GPL-3.0-or-later; see [LICENSE](LICENSE). This does not relicense any separately
published add-on.
