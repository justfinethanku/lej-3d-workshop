"""Repeated 3MF instances retain exact transformed bounds with bounded storage."""
import importlib.util
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest import mock
import weakref
import xml.etree.ElementTree as ET
import zipfile

SCRIPT = (Path(__file__).resolve().parents[1] /
          'skill/lej-3d-workshop/scripts/verify_cadquery.py')
HAS_MESH = all(importlib.util.find_spec(name) is not None
               for name in ('numpy', 'trimesh'))
NS = 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'


@unittest.skipUnless(HAS_MESH, 'Install the CAD test requirements for mesh tests')
class ThreeMFBounds(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'instances.3mf'
        self.bounds = runpy.run_path(str(SCRIPT))['three_mf_bounds']

    def fixture(self, count=1, rotation=False):
        # Asymmetric tetrahedron: transforming its AABB would overestimate it.
        root = ET.Element('model', xmlns=NS, unit='millimeter')
        resources = ET.SubElement(root, 'resources')
        mesh = ET.SubElement(ET.SubElement(resources, 'object', id='1'), 'mesh')
        vertices = ET.SubElement(mesh, 'vertices')
        for x, y, z in ((0, 0, 0), (2, 0, 0), (0, 1, 0), (0, 0, 3)):
            ET.SubElement(vertices, 'vertex', x=str(x), y=str(y), z=str(z))
        triangles = ET.SubElement(mesh, 'triangles')
        for a, b, c in ((0, 2, 1), (0, 1, 3), (0, 3, 2), (1, 2, 3)):
            ET.SubElement(triangles, 'triangle', v1=str(a), v2=str(b), v3=str(c))
        components = ET.SubElement(ET.SubElement(resources, 'object', id='2'),
                                   'components')
        ET.SubElement(components, 'component', objectid='1',
                      transform='1 0 0 0 1 0 0 0 1 0 4 0')
        build = ET.SubElement(root, 'build')
        for i in range(count):
            # Rotate by 45 degrees about Z; component placement is rotated too.
            matrix = ('0.7071067811865476 0.7071067811865476 0 '
                      '-0.7071067811865476 0.7071067811865476 0 0 0 1'
                      if rotation else '1 0 0 0 1 0 0 0 1')
            ET.SubElement(build, 'item', objectid='2',
                          transform=f'{matrix} {i * 10} 0 0')
        return root

    def save(self, root):
        with zipfile.ZipFile(self.path, 'w') as archive:
            archive.writestr('3D/3dmodel.model', ET.tostring(root))

    def test_nested_rotated_instances_use_actual_vertices(self):
        import math
        import numpy as np
        self.save(self.fixture(3, rotation=True))
        s = math.sqrt(0.5)
        np.testing.assert_allclose(self.bounds(self.path),
                                   [[-5*s, 4*s, 0], [20-2*s, 6*s, 3]])

    def test_repeated_instances_release_transformed_vertices(self):
        import numpy as np
        import trimesh
        self.save(self.fixture(64))
        original = trimesh.transform_points
        references = []
        live_counts = []

        def observe(*args, **kwargs):
            result = original(*args, **kwargs)
            references.append(weakref.ref(result))
            live_counts.append(sum(ref() is not None for ref in references))
            return result

        with mock.patch.object(trimesh, 'transform_points', observe):
            actual = self.bounds(self.path)
        np.testing.assert_allclose(actual, [[0, 4, 0], [632, 5, 3]])
        self.assertEqual(len(references), 64)
        # One current result plus at most the previous loop value, independent
        # of instance count. This checks storage ownership, not wall-clock time.
        self.assertLessEqual(max(live_counts), 2)
        self.assertTrue(all(ref() is None for ref in references))

    def test_replaced_archive_revalidates_and_recovers(self):
        import numpy as np
        self.save(self.fixture(4))
        expected = self.bounds(self.path)
        bad = self.fixture(4)
        bad.find('.//triangle').set('v1', '99')
        self.save(bad)
        for _ in range(2):
            with self.assertRaisesRegex(ValueError, 'invalid triangle indices'):
                self.bounds(self.path)
        self.save(self.fixture(4))
        np.testing.assert_array_equal(self.bounds(self.path), expected)

    def test_later_instances_still_validate_transforms_and_references(self):
        cases = {
            'nonfinite': ('transform', '1 0 0 0 1 0 0 0 1 NaN 0 0'),
            'missing': ('objectid', 'missing'),
        }
        for name, (key, value) in cases.items():
            with self.subTest(name=name):
                root = self.fixture(3)
                root.find('build')[-1].set(key, value)
                self.save(root)
                with self.assertRaises(ValueError):
                    self.bounds(self.path)
        root = self.fixture(3)
        root.find('resources')[-1].find('components/component').set('objectid', '2')
        self.save(root)
        with self.assertRaisesRegex(ValueError, 'cyclic'):
            self.bounds(self.path)


if __name__ == '__main__':
    unittest.main()
