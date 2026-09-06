# CadQuery and tool selection

CadQuery is a Python solid-modeling library. It is a strong default for holes, enclosures, connectors, repeated architectural components and controlled dimensions. Blender is a strong default for sculpting, terrain and surface detail. FreeCAD or another interactive CAD application can help with manual editing/inspection; choose based on the object and available tools. Neither category guarantees resemblance or physically accurate fit.

## Install and run

Official [installation guidance](https://cadquery.readthedocs.io/en/latest/installation.html) supports isolated Python or conda environments. Check supported Python/OS packages before installing; compiled dependencies can lag new Python releases. Keep a working environment pinned and trial upgrades separately.

Tested on macOS arm64 in September 2026: Python 3.12.9, CadQuery 2.8.0, OCP 7.9.3.1.1 and trimesh 5.1.0. From the configured workspace, its wrapper runs a script without changing its working directory:

```sh
"Shared Tools/cadquery/cq-python" path/to/build.py
```

For a fresh environment with `uv` already available, the validated installation pattern is:

```sh
uv venv --python 3.12 "Shared Tools/cadquery/.venv"
uv pip install --python "Shared Tools/cadquery/.venv/bin/python" cadquery==2.8.0 trimesh==5.1.0 numpy
```

These paths reflect the configured workspace; adapt them to your OS. Record resolved package versions after installation. The local tool folder contains a full lockfile and README. Do not assume the public skill includes that machine's runtime. Standard `venv`/pip or conda is also suitable when supported.

## Verify a first-time installation

The complete skill includes [verify_cadquery.py](../scripts/verify_cadquery.py), the same executable tryout used to check Jonathan's installation. It requires CadQuery, numpy and trimesh in the selected environment. Run it with that environment's Python and an explicit project output folder:

```sh
python /path/to/lej-3d-workshop/scripts/verify_cadquery.py --output-dir /path/to/Projects/cadquery-tryout
```

Read the generated report, exports and previews. It checks dimensional intent, valid solids, parameter changes, mesh and STEP round trips, and package structure. It writes a new timestamped subfolder inside the requested output tree, preserving earlier runs. It does not slice, connect to a printer or prove physical fit. Independently inspect the exports in your slicer before a print-ready handoff.

## Useful handles

Use named Python parameters for functional dimensions and clearances. `Workplane`, sketches, extrusions, revolutions, sweeps, lofts, booleans and selectors build feature relationships; `Assembly` represents separately named components. Prefer semantic selection over fragile face indices. Fillets and shells can fail for geometric reasons: inspect intermediate solids and adjust the actual feature, rather than suppressing errors.

Read the current [API reference](https://cadquery.readthedocs.io/en/latest/classreference.html), [selectors](https://cadquery.readthedocs.io/en/latest/selectors.html), and [examples](https://cadquery.readthedocs.io/en/latest/examples.html) as needed. Python execution is the primary agent interface; CQ-editor, Jupyter, SVG and exported previews are optional viewing paths.

A small illustrative build:

```python
from pathlib import Path
import cadquery as cq

out = Path("03-exports")
out.mkdir(parents=True, exist_ok=True)
part = cq.Workplane("XY").box(40, 24, 6).faces(">Z").workplane().hole(8)
solid = part.val()
assert solid.isValid() and len(part.solids().vals()) == 1
assert abs(solid.BoundingBox().xlen - 40) < 1e-7
cq.exporters.export(part, str(out / "plate.step"))
solid.exportStl(str(out / "plate.stl"), tolerance=0.01, angularTolerance=0.1, relative=False)
reloaded = cq.importers.importStep(str(out / "plate.step")).val()
assert reloaded.isValid()
assert abs(reloaded.Volume() - solid.Volume()) < 1e-5
```

Millimeters are the workshop convention; verify scale after every cross-tool transfer. Export tolerances control mesh approximation and should suit the actual feature scale. The example values are a starting point, not guaranteed fit clearance or universal precision.

Explore beyond this starting map. Inspect installed signatures with `inspect.signature` and package version metadata, use Python/native CAD or Blender scripting, and discover available CLI/viewer integrations. The listed operations are not a whitelist. [CQ-editor](https://github.com/CadQuery/CQ-editor), [OCP CAD Viewer](https://github.com/bernhard-42/vscode-ocp-cad-viewer), and [Jupyter visualization](https://cadquery.readthedocs.io/en/stable/vis.html) are optional researched interfaces, not installed dependencies of this skill. Stock Blender does not imply a STEP importer; use an installed importer or explicitly tessellate and verify scene scaling.

## Local validation finding

The September 6, 2026 tryout passed 29 scripted checks. Bambu Studio CLI accepted the STL as one manifold part at 40 × 24 × 6 mm. The generic CadQuery 3MF reported seven parts and 530 open edges despite a manifold flag. Use STEP plus labeled STL for this tested path; repair and revalidate generic 3MF topology/body grouping before presenting it as print-ready. This is version-specific software evidence, not physical-print proof or a claim that all CadQuery 3MF exports fail.

## Export and inspect

Consult [format/export documentation](https://cadquery.readthedocs.io/en/latest/importexport.html) for the installed version. Preserve Python source for the parametric model. STEP preserves solid geometry, not Python history. STL is a triangulated fallback. Verify names, separate bodies and colors through an assembly round trip rather than assuming metadata survives. GLB can retain named assembly nodes while splitting each CAD face into separate mesh primitives; primitive count is not solid count. CadQuery 3MF is geometry, not a fully configured Bambu Studio project; import, configure, preview layers and save through the slicer when that is the requested handoff.

Check validity, intended solid count, dimensions and volume before export; reload STEP and inspect mesh watertightness/winding/dimensions independently. Include an expected-dimension change to prove parameters actually control the model. View the output and perform slicer verification as described in [modeling](modeling.md). Software proof does not establish physical fit.

Sources checked September 6, 2026. Verify version-specific API behavior with the installed runtime before relying on a new feature.
