"""Public verifier CLI contracts, with real CAD integration when installed."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = (Path(__file__).resolve().parents[1] /
          'skill/lej-3d-workshop/scripts/verify_cadquery.py')
HAS_CAD = all(importlib.util.find_spec(name) is not None
              for name in ('cadquery', 'numpy', 'trimesh'))


class VerifierBase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.cwd = Path(self.temp.name)

    def invoke(self, *args, without_packages=False, prelude=''):
        if prelude:
            code = (prelude + '\nimport runpy, sys\n' +
                    f'sys.argv = [{str(SCRIPT)!r}] + sys.argv[1:]\n' +
                    f'runpy.run_path({str(SCRIPT)!r}, run_name="__main__")\n')
            command = [sys.executable, '-c', code]
        else:
            command = [sys.executable] + (['-S'] if without_packages else [])
            command.append(str(SCRIPT))
        return subprocess.run(
            command + list(args), cwd=self.cwd, text=True, capture_output=True,
            timeout=120, env={**os.environ, 'OMP_NUM_THREADS': '2',
                              'OPENBLAS_NUM_THREADS': '2'})

    def read_report(self, result):
        self.assertTrue((self.cwd / 'runs').is_dir(), result.stderr)
        runs = list((self.cwd / 'runs').iterdir())
        self.assertEqual(len(runs), 1, result.stderr)
        run = runs[0]
        report_path = run / 'validation.json'
        self.assertTrue(report_path.is_file(), result.stderr)
        report = json.loads(report_path.read_text())
        self.assertEqual(json.loads(result.stdout), {
            'output': str(run), 'status': report['status'],
            'checks': len(report['checks'])})
        actual_files = {p.name for p in run.iterdir() if p.name != 'validation.json'}
        self.assertEqual({f['name'] for f in report['files']}, actual_files)
        for entry in report['files']:
            data = (run / entry['name']).read_bytes()
            self.assertEqual(entry['bytes'], len(data))
            self.assertEqual(entry['sha256'], hashlib.sha256(data).hexdigest())
        return run, report


class VerifierCLI(VerifierBase):
    def test_help_works_without_optional_packages_or_creating_outputs(self):
        result = self.invoke('--help', without_packages=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('--output-dir', result.stdout)
        self.assertEqual(list(self.cwd.iterdir()), [])

    def test_missing_dependency_records_failed_run(self):
        # -S disables site-packages even in a CAD-enabled environment.
        result = self.invoke('--output-dir', 'runs', without_packages=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('cadquery', result.stderr)
        _, report = self.read_report(result)
        self.assertEqual(report['status'], 'failed')
        self.assertIn('cadquery', report['error'])
        self.assertEqual(report['checks'], [])
        self.assertEqual(report['files'], [])


@unittest.skipUnless(HAS_CAD, 'Install the CAD test requirements for real geometry tests')
class VerifierGeometry(VerifierBase):
    def test_real_exports_and_checksums_preserve_previous_run(self):
        result = self.invoke('--output-dir', 'runs')
        self.assertEqual(result.returncode, 0, result.stderr)
        run, report = self.read_report(result)
        self.assertEqual(report['status'], 'passed')
        self.assertEqual(report['units'], 'mm')
        self.assertEqual(set(report['versions']), {'cadquery', 'cadquery-ocp', 'trimesh'})
        self.assertEqual(len(report['checks']), 29)
        self.assertTrue(all(check['passed'] for check in report['checks']))
        self.assertEqual({f['name'] for f in report['files']}, {
            f'{part}.{extension}'
            for part in ('fit-plate-hole-6.0', 'fit-plate-hole-6.2', 'pin-diameter-5.8')
            for extension in ('step', 'stl', '3mf', 'svg')
        } | {'fit-study.step', 'fit-study.glb', 'rounded-tray.step', 'rounded-tray.stl'})
        volumes = {c['check']: c['actual'] for c in report['checks']
                   if c['check'].endswith('analytic volume')}
        self.assertGreater(volumes['fit-plate-hole-6.0 analytic volume'],
                           volumes['fit-plate-hole-6.2 analytic volume'])
        original = {p.name: p.read_bytes() for p in run.iterdir()}
        second = self.invoke('--output-dir', 'runs')
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertNotEqual(json.loads(second.stdout)['output'], str(run))
        self.assertEqual(len(list((self.cwd / 'runs').iterdir())), 2)
        self.assertEqual({p.name: p.read_bytes() for p in run.iterdir()}, original)

    def test_rejects_displaced_real_stl_and_retains_partial_evidence(self):
        result = self.invoke('--output-dir', 'runs', prelude='''
import trimesh
original_load = trimesh.load_mesh
def displaced_mesh(*args, **kwargs):
    mesh = original_load(*args, **kwargs)
    mesh.apply_translation([100, 0, 0])
    return mesh
trimesh.load_mesh = displaced_mesh
''')
        self.assertNotEqual(result.returncode, 0)
        _, report = self.read_report(result)
        self.assertEqual(report['status'], 'failed')
        self.assertEqual(report['error'], 'fit-plate-hole-6.0 STL bounds and volume')
        self.assertEqual(len(report['checks']), 6)
        self.assertTrue(all(c['passed'] for c in report['checks'][:-1]))
        self.assertFalse(report['checks'][-1]['passed'])
        self.assertEqual({f['name'] for f in report['files']},
                         {'fit-plate-hole-6.0.step', 'fit-plate-hole-6.0.stl'})

    def test_missing_distribution_metadata_records_failed_run(self):
        result = self.invoke('--output-dir', 'runs', prelude='''
import importlib.metadata as metadata
original_version = metadata.version
def missing_ocp_version(name):
    if name == 'cadquery-ocp':
        raise metadata.PackageNotFoundError(name)
    return original_version(name)
metadata.version = missing_ocp_version
''')
        self.assertNotEqual(result.returncode, 0)
        _, report = self.read_report(result)
        self.assertEqual(report['status'], 'failed')
        self.assertIn('cadquery-ocp', report['error'])
        self.assertEqual(report['checks'], [])
        self.assertEqual(report['files'], [])


if __name__ == '__main__':
    unittest.main()
