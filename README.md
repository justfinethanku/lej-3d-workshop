# LEJ 3D Workshop

One practical, adaptable skill for agents helping humans make physical 3D prints. Jonathan uses the same skill published here. His nonsecret setup lives in an editable User config section inside [SKILL.md](skill/lej-3d-workshop/SKILL.md); your AI can adapt that section to your workshop without creating a second edition.

The compact entrypoint routes to setup, CadQuery and Blender workflows, dimensional and visual validation, material evidence, and optional LEJ/Fleet inventory and print-library operations. It supports capable agents using Python, native tools, command-line interfaces and visual inspection. Use the techniques that fit the object; the skill does not prescribe a style or require Jonathan's hardware.

## Get started

Download the complete versioned ZIP from [Releases](https://github.com/justfinethanku/lej-3d-workshop/releases), verify its SHA-256 against that release's SHA256SUMS, and extract it. Place `lej-3d-workshop/` in your agent's skills directory, or ask another agent to read its SKILL.md directly. Keep the references with it. No Python runtime, CAD application, account, or printer connection is bundled.

Try: “Use LEJ 3D Workshop. Inspect my available tools and help adapt the User config section to my setup, then design a small dimensional test part.” Installation/setup is described in [setup](skill/lej-3d-workshop/references/setup.md). Configure only what you use; Fleet is optional.

## Updates

Back up or commit your copy before updating. Preserve the text inside the User config markers while replacing shared files from a reviewed release. Review newly added config fields and the diff; don't overwrite your printer or paths. Workflow customizations can live on a Git branch merged with upstream. See [setup/update details](skill/lej-3d-workshop/references/setup.md).

The [Workshop page](https://www.limitededitionjonathan.com/print-workshop-skill) explains the skill. The source of truth is this repository, not an independently edited website mirror. Releases use semantic versions: patch for compatible fixes, minor for added capabilities, major for incompatible workflow/config changes.

## Development and contributions

See [CONTRIBUTING](CONTRIBUTING.md), [contributors](CONTRIBUTORS.md), [changelog](CHANGELOG.md), and [testing runbook](docs/testing-runbook.md). Build a complete deterministic bundle with `python3 scripts/package.py`; output goes to ignored `dist/`. The packager checks local reference integrity and writes the archive plus SHA256SUMS. MIT licensed; tool dependencies and third-party models retain their own licenses.
