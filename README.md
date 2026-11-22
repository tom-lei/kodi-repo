# kodi-repo

Kodi add-on repository at <https://tom-lei.github.io/kodi-repo/>.

## Install

Download the repository add-on ZIP:

<https://tom-lei.github.io/kodi-repo/repository.tom-lei/repository.tom-lei-1.0.0.zip>

In Kodi, install that downloaded ZIP using **Install from zip file**. The static
index page links to the ZIP for browser downloads; the repository base URL is
<https://tom-lei.github.io/kodi-repo/>.

The catalogue initially contains only this repository add-on, so it can update
itself. No video add-ons are published yet.

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
