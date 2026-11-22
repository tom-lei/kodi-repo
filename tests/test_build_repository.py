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

            package_path = output / "repository.tom-lei" / "repository.tom-lei-1.0.0.zip"
            package = package_path.read_bytes()
            self.assertEqual(
                hashlib.sha256(package).hexdigest(),
                (output / "repository.tom-lei" / "repository.tom-lei-1.0.0.zip.sha256").read_text().strip(),
            )
            with zipfile.ZipFile(package_path) as archive:
                self.assertEqual(
                    set(archive.namelist()),
                    {
                        "repository.tom-lei/addon.xml",
                        "repository.tom-lei/LICENSE",
                        "repository.tom-lei/README.md",
                    },
                )
                manifest = archive.read("repository.tom-lei/addon.xml")
            catalogued_manifest = builder.ElementTree.fromstring(catalogue)[0]
            packaged_manifest = builder.ElementTree.fromstring(manifest)
            self.assertEqual(catalogued_manifest.attrib, packaged_manifest.attrib)
            self.assertEqual(catalogued_manifest.find("extension/dir/info").text, builder.BASE_URL + "addons.xml")
            self.assertEqual(catalogued_manifest.find("extension/dir/checksum").get("verify"), "sha256")
            self.assertIn(b"Install repository", (output / "index.html").read_bytes())

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
                    '<addon id="plugin.video.example" name="Example" version="2.3.4"/>',
                )
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


if __name__ == "__main__":
    unittest.main()
