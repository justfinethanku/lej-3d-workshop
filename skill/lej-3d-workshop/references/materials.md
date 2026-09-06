# Material planning

Apply these evidence principles with any inventory system. Inventory is not current loaded state. Unknown is unknown, not zero. Local proposals are not published downloadable profiles.

Start from the `material_source` field in User config:

- LEJ/Fleet Workshop (Jonathan's configuration): read the [Workshop data contract](workshop-data.md) for endpoints, tables and authorized writes.
- Another API: inspect that API's current contract before relying on it.
- A spreadsheet or local notes: inspect the designated file and its date; distinguish a live owner-maintained record from an old export.
- None: plan from supplied facts and manufacturer guidance, mark availability unknown, and ask only for the material choices needed to make the object usable.

None of these alternatives needs an LEJ/Fleet account. If a configured source is unavailable, say so and use another authorized source rather than guessing.

## Make a material and hardware plan

Read current products, availability, observations, printer/hotend/AMS parts, guidance, and published profile versions. Filter archived stock; preserve missing values as unknown. Separate received purchase history from available units. Keep known grams and observation coverage together: a partial measured sum is not the total stock balance.

Explain the chosen product, source of settings, required printer/nozzle/hotend/plate, compatible exact profile version, and any swaps. A family setting applies across linked products only within its documented scope; it is not a color-specific test. Manufacturer guidance, shipped slicer defaults, and inspected owner print evidence remain separate. Advertised maximum speed is not a universal printing recommendation.

Compatibility must match the actual model, nozzle diameter/material, standard or high-flow hotend, relevant side, plate, slicer/version and dependencies. A friend’s unowned printer belongs in compatibility metadata, not owned inventory. An adaptation is a new version linked to its parent and remains untested until supported by an exactly linked, physically inspected successful print. Do not copy machine/spool calibration into a universal preset.

## Record observations only when supported and authorized

A momentary AMS reading is a dated estimate, not a lasting loaded-state claim. Match the physical consumable spool/refill using a stable label, serial, or explicit identity evidence. Similar colors or the reusable reel alone do not establish identity. Ask about ambiguity; do not apply that reading to a guessed spool. Provisional identities remain provisional.

Store original amount/unit, observed time, source, evidence and honest attribution. Preserve percent as percent; grams derived from it require documented applicable starting mass and stay estimated. Do not use nominal package weight as current remaining weight. A weighed amount needs a clear net-filament basis or evidenced tare subtraction. Unknown is not zero. Corrections append and reference the prior reading; they never erase it. Refresh versions before writing and stop on a conflict for re-read/reconciliation rather than overwriting another edit.

## Preserve the plan with the exact project

Keep the exact settings used with the project: the preset or settings file, slicer version, printer/nozzle/plate, and material. When your catalog publishes verified profiles, download the selected files through owner access or a selected revocable share, verify SHA-256/size, preserve local originals, and attach exact published profile versions and resolved settings snapshots to a draft release or planned print before use; sealed releases stay immutable. Otherwise preserve the local preset or exported settings file beside the project's exports and notes. Software validation is not a physical print result. Record actual outcomes, error codes and improvement suggestions separately.

Do not silently change released files/settings, calibrate hardware, start printing, poll devices, install background jobs, or deduct material. Print estimates, printer-reported usage, and confirmed consumption stay separate from stock observations. This skill does not grant write permission beyond the user’s task.
