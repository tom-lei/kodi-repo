import hashlib
import importlib.util
import tempfile
import unittest
import zipfile
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "build_repository.py"
SPEC = importlib.util.spec_from_file_location("build_repository", SCRIPT)
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


class RepositoryBuildTests(unittest.TestCase):
    def test_build_emits_self_update_catalogue_and_exact_hashes(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            builder.build(output)

            catalogue = (output / "addons.xml").read_bytes()
            digest = (output / "addons.xml.sha256").read_text().strip()
            self.assertEqual(hashlib.sha256(catalogue).hexdigest(), digest)

            filename = f"repository.tom-lei-{builder.REPOSITORY_VERSION}.zip"
            package_path = output / "repository.tom-lei" / filename
            package = package_path.read_bytes()
            self.assertEqual(
                hashlib.sha256(package).hexdigest(),
                Path(f"{package_path}.sha256").read_text().strip(),
            )
            with zipfile.ZipFile(package_path) as archive:
                self.assertEqual(
                    set(archive.namelist()),
                    {
                        "repository.tom-lei/addon.xml",
                        "repository.tom-lei/LICENSE",
                        "repository.tom-lei/README.md",
                        "repository.tom-lei/changelog.txt",
                    },
                )
                manifest = archive.read("repository.tom-lei/addon.xml")
            catalogued_manifest = builder.ElementTree.fromstring(catalogue).find(
                f"./addon[@id='repository.tom-lei'][@version='{builder.REPOSITORY_VERSION}']"
            )
            packaged_manifest = builder.ElementTree.fromstring(manifest)
            self.assertEqual(catalogued_manifest.attrib, packaged_manifest.attrib)
            self.assertEqual(catalogued_manifest.find("extension/dir/info").text, builder.BASE_URL + "addons.xml")
            self.assertEqual(catalogued_manifest.find("extension/dir/checksum").get("verify"), "sha256")
            self.assertIn(b"Install repository", (output / "index.html").read_bytes())

    def test_existing_repository_installer_remains_available_for_updates(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            builder.build(output)
            old_path = output / "repository.tom-lei" / "repository.tom-lei-1.0.0.zip"
            old_bytes = old_path.read_bytes()
            self.assertEqual(old_bytes, (builder.PACKAGE_DIR / "repository.tom-lei-1.0.0.zip").read_bytes())
            self.assertEqual(
                hashlib.sha256(old_bytes).hexdigest(),
                Path(f"{old_path}.sha256").read_text().strip(),
            )
            root = builder.ElementTree.parse(output / "addons.xml").getroot()
            manifests = {
                addon.get("version"): addon
                for addon in root.findall("./addon[@id='repository.tom-lei']")
            }
            self.assertIn("1.0.0", manifests)
            self.assertIn(builder.REPOSITORY_VERSION, manifests)
            self.assertEqual(
                manifests["1.0.0"].findtext("extension/dir/info"),
                manifests[builder.REPOSITORY_VERSION].findtext("extension/dir/info"),
            )
            self.assertIn(
                f"repository.tom-lei-{builder.REPOSITORY_VERSION}.zip",
                (output / "index.html").read_text(encoding="utf-8"),
            )

    def test_repository_zip_is_stable_across_checkout_line_endings(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = builder.REPOSITORY_DIR
            checkout = Path(temporary)
            for name in ("addon.xml", "LICENSE", "README.md", "changelog.txt"):
                (checkout / name).write_bytes((source / name).read_bytes().replace(b"\r\n", b"\n"))
            previous = builder.REPOSITORY_DIR
            builder.REPOSITORY_DIR = checkout
            try:
                lf_zip = builder.make_repository_zip()
                for path in checkout.iterdir():
                    path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
                self.assertEqual(builder.make_repository_zip(), lf_zip)
            finally:
                builder.REPOSITORY_DIR = previous

    def test_release_package_requires_matching_addon_id_and_zip_root(self):
        with tempfile.TemporaryDirectory() as temporary:
            package_path = Path(temporary) / "wrong.zip"
            with zipfile.ZipFile(package_path, "w") as archive:
                archive.writestr(
                    "plugin.video.example/addon.xml",
                    '<addon id="plugin.video.other" name="Example" version="1.0.0"/>',
                )
            with self.assertRaisesRegex(ValueError, "does not match"):
                builder.read_release_package(package_path)

    def test_build_publishes_separately_released_zip_with_hash(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            packages = root / "packages"
            packages.mkdir()
            package_path = packages / "release.zip"
            with zipfile.ZipFile(package_path, "w") as archive:
                archive.writestr(
                    "plugin.video.example/addon.xml",
                    '<addon id="plugin.video.example" name="Example" version="2.3.4">'
                    '<extension point="xbmc.addon.metadata"><assets><icon>icon.png</icon>'
                    '</assets></extension></addon>',
                )
                archive.writestr("plugin.video.example/icon.png", b"test icon")
            package_bytes = package_path.read_bytes()
            previous_package_dir = builder.PACKAGE_DIR
            builder.PACKAGE_DIR = packages
            try:
                output = root / "site"
                builder.build(output)
            finally:
                builder.PACKAGE_DIR = previous_package_dir

            published = output / "plugin.video.example" / "plugin.video.example-2.3.4.zip"
            self.assertEqual(published.read_bytes(), package_bytes)
            self.assertEqual(
                hashlib.sha256(package_bytes).hexdigest(),
                Path(f"{published}.sha256").read_text().strip(),
            )
            addon_ids = [addon.get("id") for addon in builder.ElementTree.parse(output / "addons.xml").getroot()]
            self.assertIn("plugin.video.example", addon_ids)
            self.assertEqual((output / "plugin.video.example" / "icon.png").read_bytes(), b"test icon")


if __name__ == "__main__":
    unittest.main()
