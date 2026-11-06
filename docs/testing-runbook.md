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

Link validation uses the installed release paths, including `LICENSE` and
`VERSION` copied from the repository root. A skill reference can link to those
bundled files even though they live outside the skill source directory. Keep
release metadata at the repository root: a second `LICENSE` or `VERSION` at the
skill root fails as a duplicate release path. The tests exercise these cases and
reject missing, excluded, and outside-package link targets before writing output.

No generated content is written outside ignored `dist/`; delete that directory for cleanup. Do not use production inventory or printer jobs as a documentation smoke test. CadQuery runtime installation and geometry testing are recorded in the configured workspace's cadquery-tryout project and belong to their own validation scope.

The CAD reference Python example executed successfully in the installed CadQuery 2.8.0 environment, including valid solid, intended width, STEP round-trip validity and volume equality. Example files were temporary and removed from the workspace.

Run the public verifier with the selected CAD Python: `python skill/lej-3d-workshop/scripts/verify_cadquery.py --output-dir /tmp/lej-cadquery-check`. It needs cadquery, numpy and trimesh; writes a timestamped run only under that directory; returns nonzero for failed checks. The promoted script passed all 29 checks on macOS arm64/Python 3.12/CadQuery 2.8.0. Remove only that temporary output for cleanup. The bundle includes every maintained file in the skill folder except hidden files, caches and generated verification runs; a Markdown link to a file that is not packaged fails the build. GitHub Actions (`.github/workflows/package.yml`) runs the packager and a syntax check of the verifier on every push and pull request; it does not install CadQuery.
