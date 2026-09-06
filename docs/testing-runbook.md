# Testing runbook

## Skill and public bundle

Status: tested September 6, 2026. Packaging passed with six skill files and eight ZIP entries; source-byte equality and relative links passed. Skill-creator quick validation passed. No owner account or live data mutations required.

Run `python3 scripts/package.py` from the repository. This checks every relative Markdown reference stays in the skill package and exists, validates a single intact user-config block, packages all skill files plus license/version, and writes SHA256SUMS. Open the ZIP and compare every included byte to source. Run the skill-creator `quick_validate.py skill/lej-3d-workshop` when that tool is available. Review the main instructions for sensible behavior: a non-Bambu user must be able to customize config; a modeled part must not become a claimed physical success; an inventory read must not become a stock change.

No generated content is written outside ignored `dist/`; delete that directory for cleanup. Do not use production inventory or printer jobs as a documentation smoke test. CadQuery runtime installation and geometry testing are recorded in the configured workspace's cadquery-tryout project and belong to their own validation scope.

The CAD reference Python example executed successfully in the installed CadQuery 2.8.0 environment, including valid solid, intended width, STEP round-trip validity and volume equality. Example files were temporary and removed from the workspace.
