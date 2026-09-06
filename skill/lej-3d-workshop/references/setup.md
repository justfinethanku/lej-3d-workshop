# Setup, customization, and organization

Install the complete `lej-3d-workshop` folder, including references, in your agent's skills directory (for example `~/.codex/skills/` or `~/.claude/skills/`). Other agents can simply read its `SKILL.md` as a project instruction document. Use one canonical copy or a filesystem link where supported instead of independently maintaining mirrors.

Ask your AI: “Read LEJ 3D Workshop, inspect my available tools, and adapt its User config section to my printer and workspace. Keep useful defaults; ask about consequential unknowns.” The configuration lives inside SKILL.md. There is no private edition or separate configuration product. A different user can use just CadQuery, just Blender, or the material guidance without installing Fleet or owning an H2C.

## First-time software setup

Inspect the OS/architecture and installed tools before choosing packages. Use official installers or package distributions, record versions, and keep each CAD Python environment isolated. Install the smallest useful stack: a modeling tool, a compatible slicer, and a way to inspect output. Optional viewers are optional. Avoid modifying system Python or unrelated shell/profile configuration.

For CadQuery use the [CAD reference](cadquery.md). For Blender start with [Blender's manual](https://docs.blender.org/manual/en/latest/); for Bambu Studio use [the official repository and releases](https://github.com/bambulab/BambuStudio). Select a slicer compatible with the user's actual machine. Other CAD systems and slicers are welcome when they better fit the task.

Create a small dimensional specimen and verify its solid geometry, dimensions, exported mesh, and slicer import. A successful import alone does not establish correct units or printability. Keep the installation's commands, package versions and validation output alongside the reusable tool, with generated test artifacts in a clearly named project.

## Project files

For a substantial new project, this is a starting point, not a mandatory naming standard:

```
Projects/descriptive-name/
  01-concepts/    sources, measurements, sketches
  02-cad/         Python CAD source, parameters, validation scripts
  02-blender/     editable mesh scenes and build/render scripts, if used
  03-exports/     labeled STEP, STL, 3MF and other handoffs
  04-docs/        previews, source attribution, print notes, validation
Shared Tools/    reusable wrappers and isolated tool runtimes
```

Use paths relative to the project in reproducible scripts. Keep sources and prior versions; make a sibling repair/version rather than overwriting the only original. Put large environments/caches outside versioned artifacts and ignore them in Git. Record length units and, for modular/geographic work, origin, orientation, scale, coordinate system and shared contact surfaces.

## Updating your copy

The public release and Jonathan's working skill share one source. Users naturally customize their own copy. Before updating, save a copy or Git commit. Replace the shared skill files from the reviewed release while preserving the exact text between `USER_CONFIG_START` and `USER_CONFIG_END` in your current SKILL.md. Review upstream configuration additions and bring useful fields into your retained block; don't silently reset the user's printer or paths. Re-read the changelog, inspect the diff, and verify local links. Keep custom workflow changes as a branch and merge upstream changes normally.

If maintaining several agent installations, update the canonical copy and synchronize verified identical copies or links. The repository's release archive contains the entire skill, license and version; downloading only SKILL.md loses the conditional instructions.
