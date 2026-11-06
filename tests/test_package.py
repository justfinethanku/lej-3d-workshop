"""Release boundaries, using synthetic files in isolated temporary directories."""
import contextlib
import hashlib
import importlib.util
import io
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import mock
import zipfile


SPEC = importlib.util.spec_from_file_location(
    'workshop_package', Path(__file__).resolve().parents[1] / 'scripts/package.py')
package = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(package)


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'repo'
        self.skill = self.root / 'skill/lej-3d-workshop'
        self.skill.mkdir(parents=True)
        self.files = {
            'VERSION': b'0.1.0\n',
            'LICENSE': b'Synthetic license\n',
            'skill/lej-3d-workshop/SKILL.md': (
                b'<!-- USER_CONFIG_START -->\nexample\n<!-- USER_CONFIG_END -->\n'
                b'[Reference](references/setup.md)\n'),
            'skill/lej-3d-workshop/references/setup.md': b'Synthetic reference\n',
        }
        for name, data in self.files.items():
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        self.outside = Path(self.temp.name) / 'outside.txt'
        self.outside.write_bytes(b'Nonsecret outside-tree control\n')
        self.original_outside = self.outside.read_bytes()

    def build(self):
        with contextlib.redirect_stdout(io.StringIO()):
            package.build(self.root)
        return self.root / 'dist/lej-3d-workshop-v0.1.0.zip'

    def test_complete_deterministic_archive_and_checksum(self):
        for name in ('.private', '__pycache__/cache.pyc',
                     'cadquery-verification/run.json'):
            path = self.skill / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'Excluded fixture')
        archive = self.build()
        first = archive.read_bytes()
        with zipfile.ZipFile(archive) as bundle:
            expected = {
                'lej-3d-workshop/' + name.removeprefix('skill/lej-3d-workshop/'): data
                for name, data in self.files.items()
            }
            self.assertEqual(set(bundle.namelist()), set(expected))
            for name, data in expected.items():
                self.assertEqual(bundle.read(name), data)
        self.assertEqual(
            (archive.parent / 'SHA256SUMS').read_text(),
            f'{hashlib.sha256(first).hexdigest()}  {archive.name}\n')
        self.assertEqual(self.build().read_bytes(), first)

    def test_links_resolve_against_complete_installed_release(self):
        (self.skill / 'README.md').write_text('[License](LICENSE) [Version](VERSION)\n')
        (self.skill / 'references/setup.md').write_text(
            '[License](../LICENSE#terms) [Entry](../SKILL.md)\n')
        archive = self.build()
        with zipfile.ZipFile(archive) as bundle:
            self.assertEqual(bundle.read('lej-3d-workshop/LICENSE'), self.files['LICENSE'])
            self.assertEqual(bundle.read('lej-3d-workshop/VERSION'), self.files['VERSION'])

    def test_excluded_directories_are_not_enumerated(self):
        # Checking archive contents alone misses time spent walking local caches
        # and verification runs which must never contribute release files.
        original_scandir = os.scandir
        for relative in ('.venv', '__pycache__', 'cadquery-verification',
                         'references/.cache', 'references/cadquery-verification'):
            with self.subTest(directory=relative):
                excluded = self.skill / relative
                child = excluded / 'nested/generated.stl'
                child.parent.mkdir(parents=True)
                child.write_bytes(b'Excluded synthetic mesh\n')
                visited = []

                def scandir(path):
                    visited.append(Path(path))
                    return original_scandir(path)

                try:
                    with mock.patch('os.scandir', scandir):
                        archive = self.build()
                    self.assertNotIn(excluded, visited)
                    self.assertIn(self.skill / 'references', visited)
                    with zipfile.ZipFile(archive) as bundle:
                        self.assertEqual(len(bundle.namelist()), len(self.files))
                finally:
                    shutil.rmtree(excluded)

    def test_deep_maintained_files_survive_pruning(self):
        relative = 'assets/meshes.pyc/nested/reference.stl'
        mesh = self.skill / relative
        mesh.parent.mkdir(parents=True)
        mesh.write_bytes(b'Maintained synthetic mesh\n')
        (self.skill / 'README.md').write_text(f'[Mesh]({relative})\n')
        with zipfile.ZipFile(self.build()) as bundle:
            self.assertEqual(bundle.read('lej-3d-workshop/' + relative), mesh.read_bytes())

    def test_duplicate_metadata_paths_fail_without_silently_replacing_bytes(self):
        for name in ('LICENSE', 'VERSION'):
            with self.subTest(name=name):
                duplicate = self.skill / name
                duplicate.write_bytes(b'Distinct maintained skill bytes\n')
                try:
                    with self.assertRaisesRegex(ValueError, 'Duplicate release path'):
                        self.build()
                    self.assertFalse((self.root / 'dist').exists())
                    self.assertEqual(duplicate.read_bytes(), b'Distinct maintained skill bytes\n')
                finally:
                    duplicate.unlink()

    def test_missing_excluded_and_outside_links_fail_before_writing(self):
        excluded = self.skill / '.private'
        excluded.write_bytes(b'Not distributable\n')
        for target in ('missing.md', '.private', '../../outside.txt', '/LICENSE'):
            with self.subTest(target=target):
                (self.skill / 'README.md').write_text(f'[Invalid]({target})\n')
                with self.assertRaisesRegex(ValueError, 'Linked file is missing or not packaged'):
                    self.build()
                self.assertFalse((self.root / 'dist').exists())

    def test_symlinked_input_files_fail_before_creating_artifacts(self):
        for name in self.files:
            with self.subTest(name=name):
                path = self.root / name
                path.unlink()
                self.outside.write_bytes(self.files[name])
                path.symlink_to(self.outside)
                try:
                    with self.assertRaisesRegex(ValueError, 'Symlink'):
                        self.build()
                    self.assertFalse((self.root / 'dist').exists())
                    self.assertEqual(self.outside.read_bytes(), self.files[name])
                finally:
                    path.unlink()
                    path.write_bytes(self.files[name])
                    shutil.rmtree(self.root / 'dist', ignore_errors=True)

    def test_symlinked_skill_directories_fail(self):
        for relative in ('skill', 'skill/lej-3d-workshop',
                         'skill/lej-3d-workshop/references'):
            with self.subTest(path=relative):
                path = self.root / relative
                moved = Path(self.temp.name) / 'moved'
                path.rename(moved)
                path.symlink_to(moved, target_is_directory=True)
                try:
                    with self.assertRaisesRegex(ValueError, 'Symlink'):
                        self.build()
                    self.assertFalse((self.root / 'dist').exists())
                finally:
                    path.unlink()
                    moved.rename(path)
                    shutil.rmtree(self.root / 'dist', ignore_errors=True)

    def test_symlinked_outputs_preserve_external_files(self):
        output = self.root / 'dist'
        output.mkdir()
        for name in ('lej-3d-workshop-v0.1.0.zip', 'SHA256SUMS'):
            with self.subTest(name=name):
                target = output / name
                target.symlink_to(self.outside)
                try:
                    with self.assertRaisesRegex(ValueError, 'Symlink'):
                        self.build()
                    self.assertEqual(self.outside.read_bytes(), self.original_outside)
                    self.assertEqual(list(output.iterdir()), [target])
                finally:
                    for generated in output.iterdir():
                        generated.unlink()
                    self.outside.write_bytes(self.original_outside)

    def test_symlinked_output_directory_is_untouched(self):
        external_dir = Path(self.temp.name) / 'external-output'
        external_dir.mkdir()
        (self.root / 'dist').symlink_to(external_dir, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            self.build()
        self.assertEqual(list(external_dir.iterdir()), [])

    def test_dangling_output_symlink_does_not_create_external_file(self):
        output = self.root / 'dist'
        output.mkdir()
        missing = Path(self.temp.name) / 'missing.txt'
        (output / 'SHA256SUMS').symlink_to(missing)
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            self.build()
        self.assertFalse(missing.exists())
        self.assertFalse((output / 'lej-3d-workshop-v0.1.0.zip').exists())


if __name__ == '__main__':
    unittest.main()
