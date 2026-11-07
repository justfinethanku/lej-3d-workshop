"""CadQuery software verification; reports use mm and GLB files use meters."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import importlib.metadata as metadata
import json
import math
import platform
import xml.etree.ElementTree as ET
import zipfile


def three_mf_bounds(path):
    """Validate this fixture's mesh data and resolve its built instances in mm.

    This checks indices and scale, not manifoldness or full 3MF conformance.
    """
    import numpy as np
    import trimesh

    with zipfile.ZipFile(path) as archive:
        model = ET.fromstring(archive.read('3D/3dmodel.model'))
    ns = {'m': 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
    if model.attrib.get('unit') != 'millimeter':
        raise ValueError('3MF unit must be millimeter')
    objects = model.findall('m:resources/m:object', ns)
    resources = {obj.attrib['id']: obj for obj in objects}
    if len(resources) != len(objects):
        raise ValueError('3MF duplicate object id')

    def transform(element):
        matrix = np.eye(4)
        if 'transform' in element.attrib:
            values = [float(v) for v in element.attrib['transform'].split()]
            if len(values) != 12 or not np.isfinite(values).all():
                raise ValueError('3MF invalid transform')
            matrix[:3, :] = np.array(values).reshape(4, 3).T
        return matrix

    def vertices_for(object_id, matrix, ancestors):
        if object_id in ancestors or object_id not in resources:
            raise ValueError('3MF cyclic or missing object reference')
        obj = resources[object_id]
        mesh = obj.find('m:mesh', ns)
        components = obj.findall('m:components/m:component', ns)
        if mesh is not None and not components:
            vertices = np.array([[float(v.attrib[a]) for a in ('x', 'y', 'z')]
                                 for v in mesh.findall('m:vertices/m:vertex', ns)])
            triangles = [[int(t.attrib[a]) for a in ('v1', 'v2', 'v3')]
                         for t in mesh.findall('m:triangles/m:triangle', ns)]
            if not len(vertices) or not np.isfinite(vertices).all() or not triangles:
                raise ValueError('3MF empty mesh or nonfinite coordinate')
            if any(len(set(t)) != 3 or min(t) < 0 or max(t) >= len(vertices)
                   for t in triangles):
                raise ValueError('3MF invalid triangle indices')
            return [trimesh.transform_points(vertices, matrix)]
        if not components or mesh is not None:
            raise ValueError('3MF object must contain mesh or components')
        points = []
        for component in components:
            if any(key.endswith('path') for key in component.attrib):
                raise ValueError('3MF external component is outside this fixture')
            points.extend(vertices_for(component.attrib['objectid'],
                                       matrix @ transform(component),
                                       ancestors | {object_id}))
        return points

    points = []
    for item in model.findall('m:build/m:item', ns):
        points.extend(vertices_for(item.attrib['objectid'], transform(item), set()))
    if not points:
        raise ValueError('3MF empty build')
    vertices = np.concatenate(points)
    if not np.isfinite(vertices).all():
        raise ValueError('3MF nonfinite built coordinate')
    return np.array([vertices.min(axis=0), vertices.max(axis=0)])


def export_glb_mm(assembly, path):
    """CadQuery 2.8's glTF writer needs an explicit mm-to-m input scale."""
    import cadquery as cq
    from cadquery.occ_impl.exporters.assembly import toCAF
    from OCP.Message import Message_ProgressRange
    from OCP.RWGltf import RWGltf_CafWriter
    from OCP.TCollection import TCollection_AsciiString
    from OCP.TColStd import TColStd_IndexedDataMapOfStringString

    original_location = assembly.loc
    try:
        assembly.loc *= cq.Location((0, 0, 0), (1, 0, 0), -90)
        _, doc = toCAF(assembly, True, True, 0.01, 0.1)
        writer = RWGltf_CafWriter(TCollection_AsciiString(str(path)), True)
        writer.ChangeCoordinateSystemConverter().SetInputLengthUnit(0.001)
        if not writer.Perform(doc, TColStd_IndexedDataMapOfStringString(),
                              Message_ProgressRange()):
            raise RuntimeError('GLB export failed')
    finally:
        assembly.loc = original_location


def verify(output_dir):
    """Run CPU verification in a new directory; return its path or re-raise failure.

    Each call owns its checks and artifacts. A failure stops later exports and
    retains partial evidence without changing another call's report.
    """
    out = Path(output_dir).expanduser().resolve() / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out.mkdir(parents=True, exist_ok=False)
    report = {'units': 'mm', 'status': 'running', 'versions': {}, 'python': platform.python_version(), 'platform': platform.platform(), 'checks': []}

    def check(label, passed, **evidence):
        report['checks'].append({'check': label, 'passed': bool(passed), **evidence})
        if not passed:
            raise AssertionError(label)


    def plate(hole_diameter):
        return cq.Workplane('XY').box(40, 24, 6, centered=(True, True, False)).faces('>Z').workplane().hole(hole_diameter)


    def validate_export(name, part, expected_volume, bounds):
        solid = part.val()
        check(name + ' valid solid', solid.isValid() and len(part.solids().vals()) == 1)
        check(name + ' analytic volume', math.isclose(solid.Volume(), expected_volume, abs_tol=1e-7), actual=solid.Volume(), expected=expected_volume)
        bb = solid.BoundingBox()
        actual_bounds = [[bb.xmin, bb.ymin, bb.zmin], [bb.xmax, bb.ymax, bb.zmax]]
        check(name + ' CAD bounds', np.allclose(actual_bounds, bounds, atol=1e-7), actual=actual_bounds)
        part.export(str(out / (name + '.step')))
        imported = cq.importers.importStep(str(out / (name + '.step')))
        ibb = imported.val().BoundingBox()
        check(name + ' STEP roundtrip', imported.val().isValid() and len(imported.solids().vals()) == 1 and math.isclose(imported.val().Volume(), expected_volume, abs_tol=1e-6) and np.allclose([[ibb.xmin, ibb.ymin, ibb.zmin], [ibb.xmax, ibb.ymax, ibb.zmax]], bounds, atol=1e-6), volume=imported.val().Volume())
        # Shape exporter explicitly disables relative chord tolerance.
        solid.exportStl(str(out / (name + '.stl')), tolerance=0.01, angularTolerance=0.1, relative=False)
        mesh = trimesh.load_mesh(out / (name + '.stl'))
        check(name + ' STL watertight and oriented', mesh.is_watertight and mesh.is_winding_consistent and mesh.volume > 0, faces=len(mesh.faces))
        check(name + ' STL bounds and volume', np.allclose(mesh.bounds, bounds, atol=0.02) and abs(mesh.volume / expected_volume - 1) < 0.001, bounds=mesh.bounds.tolist(), volume=float(mesh.volume))
        part.export(str(out / (name + '.3mf')), tolerance=0.01, angularTolerance=0.1)
        label = name + ' 3MF mesh, millimeter units and bounds'
        try:
            mesh_bounds = three_mf_bounds(out / (name + '.3mf'))
        except (ValueError, KeyError, ET.ParseError, zipfile.BadZipFile) as error:
            check(label, False, error=str(error))
        check(label, np.allclose(mesh_bounds, bounds, atol=0.02, rtol=0),
              bounds=mesh_bounds.tolist())
        part.export(str(out / (name + '.svg')), opt={'width': 900, 'height': 600, 'projectionDir': (1, -1, 1), 'showAxes': False, 'showHidden': False})

    try:
        # Keep optional imports and metadata failures inside this run's report.
        import cadquery as cq
        import numpy as np
        import trimesh
        for package in ('cadquery', 'cadquery-ocp', 'trimesh'):
            report['versions'][package] = metadata.version(package)
        for diameter in (6.0, 6.2):
            part = plate(diameter)
            validate_export(f'fit-plate-hole-{diameter:.1f}', part, 40*24*6 - math.pi*(diameter/2)**2*6, [[-20,-12,0],[20,12,6]])
            radii = [f._geomAdaptor().Cylinder().Radius() for f in part.val().Faces() if f.geomType() == 'CYLINDER']
            check(f'hole {diameter} cylindrical face radius', len(radii) == 1 and math.isclose(radii[0], diameter/2, abs_tol=1e-8), radii=radii)
        # Separate pin demonstrates intentional diametral clearance; no claim of physical fit.
        pin = cq.Workplane('XY').circle(2.9).extrude(10)
        validate_export('pin-diameter-5.8', pin, math.pi*2.9**2*10, [[-2.9,-2.9,0],[2.9,2.9,10]])
        assembly = cq.Assembly(name='fit-study')
        assembly.add(plate(6.2), name='plate', color=cq.Color(0.2,0.45,0.8))
        assembly.add(pin.translate((30,0,0)), name='pin', color=cq.Color(0.95,0.55,0.15))
        assembly.export(str(out / 'fit-study.step'))
        export_glb_mm(assembly, out / 'fit-study.glb')
        check('assembly STEP retains two solids', len(cq.importers.importStep(str(out / 'fit-study.step')).solids().vals()) == 2)
        scene = trimesh.load(out / 'fit-study.glb')
        check('assembly GLB retains named part nodes', {'plate', 'pin'}.issubset(scene.graph.nodes), geometries=list(scene.geometry), note='CAD faces may become separate GLB primitives')
        for label, expected in [('plate', [[-20,-12,0],[20,12,6]]),
                                ('pin', [[27.1,-2.9,0],[32.9,2.9,10]])]:
            meshes = []
            pending = [label]
            # Follow scene instances, including parent scale/placement. Geometry
            # names and local extents alone say nothing about the displayed model.
            while pending:
                node = pending.pop()
                pending.extend(scene.graph.transforms.children.get(node, []))
                matrix, geometry = scene.graph.get(node)
                if geometry is not None:
                    mesh = scene.geometry[geometry].copy()
                    mesh.apply_transform(matrix)
                    # glTF is meters and Y-up; report comparisons in CAD mm/Z-up.
                    mesh.apply_transform([[1000,0,0,0],[0,0,-1000,0],
                                          [0,1000,0,0],[0,0,0,1]])
                    meshes.append(mesh)
            grouped = trimesh.util.concatenate(meshes)
            grouped.merge_vertices(merge_tex=True, merge_norm=True)
            check(f'GLB {label} grouped solid bounds and watertightness',
                  grouped.is_watertight and np.isfinite(grouped.vertices).all()
                  and np.allclose(grouped.bounds, expected, atol=0.02, rtol=0),
                  bounds_mm=grouped.bounds.tolist())
        # Small additional feature stress test; independent from analytic fixture.
        tray = cq.Workplane('XY').box(48,32,12,centered=(True,True,False)).faces('>Z').shell(-2).edges('|Z').fillet(1)
        check('shell and fillet valid', tray.val().isValid() and len(tray.solids().vals()) == 1)
        tray.export(str(out / 'rounded-tray.step'))
        tray.val().exportStl(str(out / 'rounded-tray.stl'), tolerance=0.01, relative=False)
        check('shell fillet mesh watertight', trimesh.load_mesh(out / 'rounded-tray.stl').is_watertight)
        report['status'] = 'passed'
    except Exception as error:
        report['status'] = 'failed'
        report['error'] = str(error)
        raise
    finally:
        report['files'] = [{'name': p.name, 'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(out.iterdir()) if p.is_file()]
        (out / 'validation.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps({'output': str(out), 'status': report['status'], 'checks': len(report['checks'])}, indent=2))
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=Path.cwd() / 'cadquery-verification', help='Parent folder for a new timestamped run; existing runs are preserved.')
    args = parser.parse_args(argv)
    verify(args.output_dir)


if __name__ == '__main__':
    main()
