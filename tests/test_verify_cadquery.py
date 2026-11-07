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

    def read_report(self, result, folder='runs'):
        self.assertTrue((self.cwd / folder).is_dir(), result.stderr)
        runs = list((self.cwd / folder).iterdir())
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

    def test_loading_helpers_has_no_cli_or_filesystem_side_effects(self):
        for arguments in ([], ['--unrelated-host-argument']):
            with self.subTest(arguments=arguments):
                code = ("import runpy, sys\n"
                        f"sys.argv = ['host-program'] + {arguments!r}\n"
                        f"module = runpy.run_path({str(SCRIPT)!r})\n"
                        "assert callable(module['three_mf_bounds'])\n"
                        "assert callable(module['export_glb_mm'])\n")
                result = subprocess.run([sys.executable, '-S', '-c', code],
                                        cwd=self.cwd, text=True, capture_output=True,
                                        timeout=30)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, '')
                self.assertEqual(result.stderr, '')
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
    def test_success_failure_success_share_no_run_state(self):
        import contextlib
        import io
        import runpy
        from unittest import mock
        import cadquery as cq

        verify = runpy.run_path(str(SCRIPT))['verify']
        parent = self.cwd / 'runs'
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            first = verify(parent)
            saved = {p.name: p.read_bytes() for p in first.iterdir()}
            original_export = cq.Workplane.export

            def fail_3mf(part, path, *args, **kwargs):
                if str(path).endswith('.3mf'):
                    Path(path).write_bytes(b'partial export from second run')
                    raise RuntimeError('second run export failed')
                return original_export(part, path, *args, **kwargs)

            with mock.patch.object(cq.Workplane, 'export', fail_3mf):
                with self.assertRaisesRegex(RuntimeError, 'second run export failed'):
                    verify(parent)
            third = verify(parent)

        self.assertNotEqual(first, third)
        self.assertEqual({p.name: p.read_bytes() for p in first.iterdir()}, saved)
        reports = [json.loads((run / 'validation.json').read_text())
                   for run in sorted(parent.iterdir())]
        self.assertEqual([r['status'] for r in reports], ['passed', 'failed', 'passed'])
        self.assertEqual([len(r['checks']) for r in reports], [29, 6, 29])
        self.assertEqual([len(r['files']) for r in reports], [16, 3, 16])
        self.assertEqual(reports[0]['checks'], reports[2]['checks'])
        self.assertEqual(reports[1]['error'], 'second run export failed')
        self.assertNotIn('error', reports[2])
        for run, report in zip(sorted(parent.iterdir()), reports):
            for entry in report['files']:
                data = (run / entry['name']).read_bytes()
                self.assertEqual(entry['bytes'], len(data))
                self.assertEqual(entry['sha256'], hashlib.sha256(data).hexdigest())

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
        # Independently check glTF's meter coordinates, including its Y-up
        # rotation and the pin's placement. A 40 mm plate must not span 40 m.
        import numpy as np
        import trimesh
        scene = trimesh.load(run / 'fit-study.glb')
        self.assertTrue(np.allclose(scene.bounds,
                                   [[-0.020, 0, -0.012], [0.0329, 0.010, 0.012]],
                                   atol=0.00002, rtol=0))
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

    def test_rejects_malformed_3mf_mesh_and_build(self):
        # Mutate real on-disk archives after export, before verification.
        mutations = {
            'scale': "for v in vertices:\n            v.set('x', str(float(v.get('x')) * 25.4))",
            'nonfinite': "vertices[0].set('x', 'NaN')",
            'outside-index': "triangles[0].set('v1', '999999')",
            'negative-index': "triangles[0].set('v1', '-1')",
            'repeated-index': "triangles[0].set('v1', triangles[0].get('v2'))",
            'fractional-index': "triangles[0].set('v1', '1.5')",
            'units': "model.set('unit', 'inch')",
            'build-scale': "model.find('m:build/m:item', ns).set('transform', '25.4 0 0 0 25.4 0 0 0 25.4 0 0 0')",
            'build-missing': "model.find('m:build/m:item', ns).set('objectid', 'missing')",
            'cycle': "model.find('.//m:component', ns).set('objectid', model.find('m:build/m:item', ns).get('objectid'))",
            'empty-build': "model.find('m:build', ns).clear()",
        }
        prelude = '''
import cadquery as cq
import zipfile, xml.etree.ElementTree as ET
original_export = cq.Workplane.export
def corrupt_archive(self, path, *args, **kwargs):
    result = original_export(self, path, *args, **kwargs)
    if str(path).endswith('.3mf'):
        with zipfile.ZipFile(path) as archive:
            files = {name: archive.read(name) for name in archive.namelist()}
        model = ET.fromstring(files['3D/3dmodel.model'])
        ns = {'m': 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
        vertices = model.findall('.//m:vertex', ns)
        triangles = model.findall('.//m:triangle', ns)
        MUTATION
        files['3D/3dmodel.model'] = ET.tostring(model)
        with zipfile.ZipFile(path, 'w') as archive:
            for name, data in files.items():
                archive.writestr(name, data)
    return result
cq.Workplane.export = corrupt_archive
'''
        for name, mutation in mutations.items():
            with self.subTest(name=name):
                folder = 'runs-' + name
                result = self.invoke('--output-dir', folder,
                                     prelude=prelude.replace('MUTATION', mutation))
                self.assertNotEqual(result.returncode, 0, result.stdout)
                _, report = self.read_report(result, folder)
                self.assertEqual(report['status'], 'failed')
                self.assertEqual(report['error'],
                                 'fit-plate-hole-6.0 3MF mesh, millimeter units and bounds')
                self.assertTrue(all(c['passed'] for c in report['checks'][:-1]))
                self.assertFalse(report['checks'][-1]['passed'])
                self.assertEqual(len(report['checks']), 7)
                self.assertEqual({f['name'] for f in report['files']}, {
                    'fit-plate-hole-6.0.' + suffix for suffix in ('step', 'stl', '3mf')})

    def test_rejects_glb_scene_scale_and_placement(self):
        prelude = '''
import pathlib, struct, json, trimesh
original_load = trimesh.load
def corrupt_glb(path, *args, **kwargs):
    path = pathlib.Path(path)
    if path.suffix == '.glb':
        data = path.read_bytes()
        length, kind = struct.unpack_from('<II', data, 12)
        model = json.loads(data[20:20 + length])
        MUTATION
        payload = json.dumps(model).encode()
        payload += b' ' * (-len(payload) % 4)
        rest = data[20 + length:]
        path.write_bytes(struct.pack('<III', 0x46546c67, 2, 20 + len(payload) + len(rest))
                         + struct.pack('<II', len(payload), kind) + payload + rest)
    return original_load(path, *args, **kwargs)
trimesh.load = corrupt_glb
'''
        for name, mutation in {
            'scale': "model['nodes'][0]['scale'] = [25.4, 25.4, 25.4]",
            'placement': "next(n for n in model['nodes'] if n.get('name') == 'pin')['translation'] = [0.1, 0, 0]",
        }.items():
            with self.subTest(name=name):
                folder = 'runs-' + name
                result = self.invoke('--output-dir', folder,
                                     prelude=prelude.replace('MUTATION', mutation))
                self.assertNotEqual(result.returncode, 0, result.stdout)
                _, report = self.read_report(result, folder)
                self.assertEqual(report['status'], 'failed')
                self.assertIn('grouped solid bounds and watertightness', report['error'])
                self.assertFalse(report['checks'][-1]['passed'])
                self.assertNotIn('rounded-tray.step', {f['name'] for f in report['files']})

    def test_export_exception_retains_partial_files_and_stops_later_exports(self):
        result = self.invoke('--output-dir', 'runs', prelude='''
import cadquery as cq
from pathlib import Path
original_export = cq.Workplane.export
def failed_export(self, path, *args, **kwargs):
    if str(path).endswith('.3mf'):
        Path(path).write_bytes(b'partial nonsecret export')
        raise RuntimeError('injected 3MF export failure')
    return original_export(self, path, *args, **kwargs)
cq.Workplane.export = failed_export
''')
        self.assertNotEqual(result.returncode, 0)
        _, report = self.read_report(result)
        self.assertEqual(report['status'], 'failed')
        self.assertEqual(report['error'], 'injected 3MF export failure')
        self.assertTrue(all(c['passed'] for c in report['checks']))
        self.assertEqual(len(report['checks']), 6)
        self.assertEqual({f['name'] for f in report['files']}, {
            'fit-plate-hole-6.0.' + suffix for suffix in ('step', 'stl', '3mf')})

    def test_glb_writer_failure_records_failed_run(self):
        result = self.invoke('--output-dir', 'runs', prelude='''
import OCP.RWGltf as gltf
original_writer = gltf.RWGltf_CafWriter
class FailedWriter:
    def __init__(self, *args):
        self.writer = original_writer(*args)
    def ChangeCoordinateSystemConverter(self):
        return self.writer.ChangeCoordinateSystemConverter()
    def Perform(self, *args):
        return False
gltf.RWGltf_CafWriter = FailedWriter
''')
        self.assertNotEqual(result.returncode, 0)
        _, report = self.read_report(result)
        self.assertEqual(report['status'], 'failed')
        self.assertEqual(report['error'], 'GLB export failed')
        files = {f['name'] for f in report['files']}
        self.assertIn('fit-study.step', files)
        self.assertNotIn('fit-study.glb', files)
        self.assertNotIn('rounded-tray.step', files)


if __name__ == '__main__':
    unittest.main()
