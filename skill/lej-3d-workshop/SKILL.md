---
name: lej-3d-workshop
description: Design, repair, validate, and prepare physical 3D prints with CAD, Blender, slicers, material planning, and preserved project files. Use for a complete print workflow or any of its stages.
---

# LEJ 3D Workshop

A practical workshop for humans and capable agents. Choose tools to serve the object: precise parts, architectural models, sculpture, experiments, or combinations. These are working defaults, not a fixed aesthetic or a limit on techniques. The public download is the same skill Jonathan uses.

## Start with the person and the object

Read the user config below and the project's own instructions. For a new user, help their AI adapt this section **in this SKILL.md**, retaining useful parts of the example setup. Discover available software and existing files first; ask for distinctions that materially affect fit, safety, cost, or usability. Record unknowns honestly. An absent Fleet account or different printer does not prevent ordinary modeling.

Keep configuration nonsecret: tool locations, hardware, preferences, and references are useful; credentials, private tokens, receipt links, and passwords belong in the user's credential system. Expand `~` using the current user's home directory when a tool does not do it automatically. Never assume another user has Jonathan's directories or inventory.

<!-- USER_CONFIG_START -->
## User config — edit this section for your workshop

These labeled fields are editable and extensible, not a fixed schema or allowed-values list. Add distinctions that help your AI work.

- `owner`: Jonathan Edwards; macOS interactive workstation.
- `workspace`: `~/AUTOMATION/3D Prints`; projects under `Projects/`, reusable local tools under `Shared Tools/`.
- `printer`: Bambu Lab H2C.
- `default_nozzle`: 0.4 mm; choose another when detail, strength, or material warrants it.
- `slicer`: Bambu Studio, matching H2C profile. Verify the installed profile's current printable envelope and hardware before final slicing.
- `multicolor`: available; keep named material bodies easy to remap. Loaded colors, AMS layout, plate, installed nozzle, and remaining material are unknown until observed.
- `modeling_tools`: CadQuery for dimensional solid geometry; Blender for mesh, terrain, organic form, detail and visual presentation; combine freely. Existing helper: `Shared Tools/blender-cli`. CadQuery setup: `Shared Tools/cadquery/` (inspect its README for this installation's commands).
- `project_defaults`: millimeters, preserved editable source, reproducible build scripts when helpful; substantial projects use the organization below. Prefer support-free orientation when it suits the design.
- `material_source`: LEJ public API and owner Fleet inventory. Other options include your API, spreadsheet, local notes, none, or a custom source; identify its location and authority here.
- `inventory_library`: LEJ Workshop at `https://www.limitededitionjonathan.com/print-inventory` and `/print-library`. Public APIs: `/api/print-inventory` and `/api/print-filament` on that host. Fleet is Jonathan's canonical inventory and preservation service; other users may substitute their own catalog or local records.
- `fleet_access` (when enrolled): discover resources using `fleet resources` / `fleet resource`; credentials only through `fleet get`. No LAN access assumed. Local CSV/Numbers exports are historical snapshots.
- `communication`: plain language; concise updates; distinguish measured facts, assumptions, software validation, and physically inspected results. Questions and planning requests are not authorization to change files or publish.
- `config_provenance`: initial public setup supplied by Jonathan, September 2026. Refresh drift-prone hardware/software facts during use; add the adapting user's distinctions here.
<!-- USER_CONFIG_END -->

## Choose only the guidance needed now

| Work | Read |
| --- | --- |
| First install, adapting this skill, software setup, updates | [Setup and organization](references/setup.md) |
| Parametric modeling, CadQuery commands, export/viewer choices | [CAD and tool selection](references/cadquery.md) |
| Creative geometry, map accuracy, assemblies, print checks and delivery | [Modeling and verification](references/modeling.md) |
| Filament, hardware, settings, spool evidence | [Material planning](references/materials.md) |
| LEJ/Fleet inventory, profiles, releases, authorized data operations | [Workshop data contract](references/workshop-data.md) |

Read the relevant reference, not the entire collection. Use current official tool documentation for unfamiliar or changing APIs. A strong agent should write and run scripts, inspect geometry numerically, view results, and use a GUI where it supplies evidence unavailable from code. Use the best available tool rather than imitating a manual click sequence unnecessarily.

## Working approach

Start from the desired object, key measurements, source evidence and physical constraints. Inspect existing models before replacing them. Make reasonable reversible design choices and a useful preview; keep uncertain dimensions and colors easy to change. Explore alternatives when they help the user choose, without turning every task into a mandatory design ceremony.

For larger projects, preserve source and prior versions, separate generated files, and agree shared units/origin/interfaces before parallel modeling. A useful default layout is `01-concepts/`, `02-cad/` or `02-blender/`, `03-exports/`, `04-docs/`. Adapt it to existing project conventions. Keep caches and environments out of deliverable folders.

Before handoff, check dimensions, sound geometry, fit, exported-file round trips, and print preparation at a depth appropriate to the work. Give useful previews and concise print notes. A generic 3MF mesh is not automatically a configured slicer project. Label software-only outcomes accurately: **print-ready, not physically proven** only after required software checks pass; otherwise identify what remains unverified.

Preserve exact released files and evidence. Material estimates do not change inventory. Designing or slicing does not by itself authorize sending a printer job, changing stock, or publishing files; follow the user's actual scope without repeated permission questions for work already authorized.
