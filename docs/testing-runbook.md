# Testing runbook

## Skill and public bundle

Status: tested September 6, 2026. Packaging passed with eight skill files and ten ZIP entries; source-byte equality and relative links passed. Skill-creator quick validation passed. No owner account or live data mutations required.

Run `python3 scripts/package.py` from the repository. This checks every relative Markdown reference stays in the skill package and exists, validates a single intact user-config block, packages all skill files plus license/version, and writes SHA256SUMS. Open the ZIP and compare every included byte to source. Run the skill-creator `quick_validate.py skill/lej-3d-workshop` when that tool is available. Review the main instructions for sensible behavior: a non-Bambu user must be able to customize config; a modeled part must not become a claimed physical success; an inventory read must not become a stock change.

Run `python3 -m unittest discover -s tests -v` for isolated release-boundary tests.
They check complete deterministic ZIP contents and checksums, reject symlinked
inputs (including skill directories and LICENSE/VERSION), and ensure symlinked
output paths cannot overwrite files outside the release directory. The fixtures
use synthetic data and require only the Python standard library. CI runs them
alongside the packager and verifier syntax check.

Packaging tests also verify that excluded directories are never enumerated,
including nested hidden caches and generated verification runs. Maintained files
in deeper directories must still be included and local links must resolve.

Link validation uses the installed release paths, including `LICENSE` and
`VERSION` copied from the repository root. A skill reference can link to those
bundled files even though they live outside the skill source directory. Keep
release metadata at the repository root: a second `LICENSE` or `VERSION` at the
skill root fails as a duplicate release path. The tests exercise these cases and
reject missing, excluded, and outside-package link targets before writing output.

The packager writes only to ignored `dist/`; remove that directory to clean up its output. Test discovery also creates Python caches, and the optional CAD procedure creates `.venv/`. The verifier writes under its selected output directory. Keep useful verification evidence before cleanup. Do not use production inventory or printer jobs as a documentation smoke test.

## CAD verifier regression tests

The standard-library test command also checks that verifier help works without
CAD packages and a missing dependency produces a failed `validation.json` report.
The real-geometry tests skip when CadQuery, NumPy, or trimesh is absent.
Install the test environment to run all nine verifier tests:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r tests/requirements-cad.txt
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 .venv/bin/python -m unittest discover -s tests -v
```

Use Python 3.12. The pinned direct dependencies were exercised on Linux arm64;
CI runs the same geometry suite on Linux x86-64. The tests execute the public CLI
in temporary directories. They verify all 29 checks, all 16 export hashes and
sizes, the volume change between hole diameters, and preservation of a previous
run. A second case displaces the real reloaded STL by 100 mm and requires a
nonzero exit, the failed bounds check, and checksummed partial exports. Another
case injects missing OCP package metadata and requires a failed report rather
than an empty run directory. These are software checks; they do not validate a
slicer profile or physical print. Temporary exports are removed by the tests;
remove `.venv/` to clean up the installed test environment.

The geometry suite also corrupts real 3MF exports with scaled coordinates,
invalid triangle indices, nonfinite values, wrong units, and missing or cyclic
build references. It changes GLB scene scale and pin placement and independently
checks that the 40 mm plate spans 0.04 meters in the exported GLB. Each corrupted
case must fail, retain checksummed partial files, and stop subsequent exports.
Exporter exceptions and a false GLB writer result must also retain failed reports.

The CAD reference Python example executed successfully in the installed CadQuery 2.8.0 environment, including valid solid, intended width, STEP round-trip validity and volume equality. Example files were temporary and removed from the workspace.

Run the public verifier with the selected CAD Python: `python skill/lej-3d-workshop/scripts/verify_cadquery.py --output-dir /tmp/lej-cadquery-check`. It needs cadquery, numpy and trimesh; writes a timestamped run only under that directory; returns nonzero for failed checks. The promoted script passed all 29 checks on macOS arm64/Python 3.12/CadQuery 2.8.0. Remove only that temporary output for cleanup. The bundle includes every maintained file in the skill folder except hidden files, caches and generated verification runs; a Markdown link to a file that is not packaged fails the build. GitHub Actions (`.github/workflows/package.yml`) runs the package checks and a separate CAD verifier job with the pinned test dependencies on every push and pull request.

## Documentation setup smoke test

The public setup and CAD procedures were exercised on November 6, 2026, on
Linux arm64 with Python 3.12.13. The existing v0.1.0 release assets passed both
`sha256sum -c SHA256SUMS` and `shasum -a 256 -c SHA256SUMS`; extraction retained
the complete installable folder. A fresh uv environment under a path containing
`Shared Tools/` installed the CAD stack. Both the published bundle and a locally
built source bundle passed 29 verifier checks and produced 16 exports each.
The CAD reference's Python example also passed its STEP round-trip assertions.

To repeat, follow [release setup](../skill/lej-3d-workshop/references/setup.md)
in a new staging directory and [CAD installation and verification](../skill/lej-3d-workshop/references/cadquery.md)
from an isolated workshop workspace. Substitute the extracted skill's absolute
path in the verifier command. Keep the resolved package list and
`validation.json` as your setup evidence. Test source changes with a freshly
built bundle as well; an existing release does not contain Unreleased fixes.

The current-source verifier's help and missing-dependency report were also
checked without site-packages. No macOS/Windows installation, uv bootstrap,
Blender/slicer import, printer connection, or physical print was exercised in
this Linux smoke test. These limits are separate from historical macOS results.
