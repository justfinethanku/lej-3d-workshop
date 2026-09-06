"""Reproducible CadQuery software verification; all dimensions in millimeters."""
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
import cadquery as cq
import numpy as np
import trimesh

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output-dir', type=Path, default=Path.cwd() / 'cadquery-verification', help='Parent folder for a new timestamped run; existing runs are preserved.')
args = parser.parse_args()
OUT = args.output_dir.expanduser().resolve() / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
OUT.mkdir(parents=True, exist_ok=False)
report = {'units': 'mm', 'status': 'running', 'versions': {p: metadata.version(p) for p in ('cadquery', 'cadquery-ocp', 'trimesh')}, 'python': platform.python_version(), 'platform': platform.platform(), 'checks': []}


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
    part.export(str(OUT / (name + '.step')))
    imported = cq.importers.importStep(str(OUT / (name + '.step')))
    ibb = imported.val().BoundingBox()
    check(name + ' STEP roundtrip', imported.val().isValid() and len(imported.solids().vals()) == 1 and math.isclose(imported.val().Volume(), expected_volume, abs_tol=1e-6) and np.allclose([[ibb.xmin, ibb.ymin, ibb.zmin], [ibb.xmax, ibb.ymax, ibb.zmax]], bounds, atol=1e-6), volume=imported.val().Volume())
    # Shape exporter explicitly disables relative chord tolerance.
    solid.exportStl(str(OUT / (name + '.stl')), tolerance=0.01, angularTolerance=0.1, relative=False)
    mesh = trimesh.load_mesh(OUT / (name + '.stl'))
    check(name + ' STL watertight and oriented', mesh.is_watertight and mesh.is_winding_consistent and mesh.volume > 0, faces=len(mesh.faces))
    check(name + ' STL bounds and volume', np.allclose(mesh.bounds, bounds, atol=0.02) and abs(mesh.volume / expected_volume - 1) < 0.001, bounds=mesh.bounds.tolist(), volume=float(mesh.volume))
    part.export(str(OUT / (name + '.3mf')), tolerance=0.01, angularTolerance=0.1)
    with zipfile.ZipFile(OUT / (name + '.3mf')) as archive:
        model = ET.fromstring(archive.read('3D/3dmodel.model'))
        ns = {'m': 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
        vertices = model.findall('.//m:vertex', ns)
        triangles = model.findall('.//m:triangle', ns)
        check(name + ' 3MF mesh and millimeter units', model.attrib.get('unit') == 'millimeter' and bool(vertices) and bool(triangles), vertices=len(vertices), triangles=len(triangles))
    part.export(str(OUT / (name + '.svg')), opt={'width': 900, 'height': 600, 'projectionDir': (1, -1, 1), 'showAxes': False, 'showHidden': False})

try:
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
    assembly.export(str(OUT / 'fit-study.step'))
    assembly.export(str(OUT / 'fit-study.glb'))
    check('assembly STEP retains two solids', len(cq.importers.importStep(str(OUT / 'fit-study.step')).solids().vals()) == 2)
    scene = trimesh.load(OUT / 'fit-study.glb')
    check('assembly GLB retains named part nodes', {'plate', 'pin'}.issubset(scene.graph.nodes), geometries=list(scene.geometry), note='CAD faces may become separate GLB primitives')
    for label, expected in [('plate', [40,24,6]), ('pin', [5.8,5.8,10])]:
        grouped = trimesh.util.concatenate([mesh for name, mesh in scene.geometry.items() if name == label or name.startswith(label + '_')])
        grouped.merge_vertices(merge_tex=True, merge_norm=True)
        check(f'GLB {label} grouped solid bounds and watertightness', grouped.is_watertight and np.allclose(grouped.extents, expected, atol=0.02), extents=grouped.extents.tolist())
    # Small additional feature stress test; independent from analytic fixture.
    tray = cq.Workplane('XY').box(48,32,12,centered=(True,True,False)).faces('>Z').shell(-2).edges('|Z').fillet(1)
    check('shell and fillet valid', tray.val().isValid() and len(tray.solids().vals()) == 1)
    tray.export(str(OUT / 'rounded-tray.step'))
    tray.val().exportStl(str(OUT / 'rounded-tray.stl'), tolerance=0.01, relative=False)
    check('shell fillet mesh watertight', trimesh.load_mesh(OUT / 'rounded-tray.stl').is_watertight)
    report['status'] = 'passed'
except Exception as error:
    report['status'] = 'failed'
    report['error'] = str(error)
    raise
finally:
    report['files'] = [{'name': p.name, 'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(OUT.iterdir()) if p.is_file()]
    (OUT / 'validation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'output': str(OUT), 'status': report['status'], 'checks': len(report['checks'])}, indent=2))
