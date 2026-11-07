# Changelog

## Unreleased

- Isolate each CAD verification run's report and exports. Loading geometry
  helpers no longer parses host arguments, creates directories, or runs CAD;
  CLI checks and failed-run evidence remain unchanged.

- Reject malformed 3MF mesh indices, nonfinite coordinates, missing/cyclic build
  references, and incorrect built dimensions. Check GLB scene placement and
  convert the verifier's millimeter models to glTF meters; CadQuery 2.8's default
  GLB export made the 40 mm fixture span 40 meters. Retain failed export evidence.
- Document executable release checksum/extraction steps, a tested isolated CAD
  setup, verifier success/failure results, runtime cleanup, and the distinction
  between published v0.1.0 and current source behavior.

- Prune hidden folders, caches, and generated verification runs before release
  traversal, so local working files do not slow packaging or inflate its memory
  use. Preserve maintained files and deterministic archive bytes.
- Exercise the public CAD verifier with real exports, checksum checks, preserved
  prior runs, and a displaced-mesh failure in CI. Keep failure reports for
  missing dependencies or package metadata, and allow help without CAD packages.
- Validate links and write archive bytes from one complete release manifest,
  including the root LICENSE and VERSION. Reject skill files that would collide
  with those metadata paths instead of silently replacing their contents.
- Reject symlinked release inputs and output paths before packaging, preventing
  outside files from entering the ZIP or being overwritten by release artifacts.
- Run isolated packaging boundary and deterministic archive tests in CI.

## 0.1.0 — 2026-09-06

- Initial public/personal LEJ 3D Workshop skill with one embedded editable user configuration.
- Consolidated workshop-material-planning workflow and its inventory/profile evidence rules.
- Added CadQuery, hybrid CAD/Blender, setup, organization, validation and delivery guidance.
- Added MIT licensing, contribution guidance, versioned complete bundle and integrity checks.
- Included the executable 29-check CadQuery tryout and portable bundle README.
- Packaging includes every maintained skill file, fails on links to unpackaged files, and runs in GitHub Actions.
