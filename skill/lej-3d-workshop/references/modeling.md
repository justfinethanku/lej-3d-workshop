# Modeling, evidence, and delivery

## Geometry and creative choices

Use parametric solids for dimensions and relationships that must remain reliable through edits. Use mesh tools for sculpted forms, terrain, ornament and texture. Combine them when useful: maintain the CAD source, export a documented mesh tolerance, and preserve Blender edits separately. STEP carries exact geometry but not the original CadQuery feature program; keep the Python source.

A 0.4 mm nozzle is a design constraint, not a ban on detail: inspect whether small features survive the intended extrusion and layers. Avoid zero-thickness surfaces, disconnected decorative islands and accidentally fragile walls. Design clearances as parameters and verify them with a small physical coupon when actual fit matters. Printer, material, orientation and process affect fit even when CAD dimensions are exact.

Keep intended colors/materials as separately named bodies. Geometry defines regions; the slicer maps actual loaded material. Add alignment, connectors or split parts when they improve fabrication, serviceability, or scale. Prefer sensible print orientation, but use supports or another process when that serves the result. Record strength-critical load direction and uncertain tolerances.

## Maps and architecture

Favor local/government GIS and current aerial imagery for boundaries, LiDAR/DEM for terrain and height, OpenStreetMap for initial roads/footprints, and photo-based correction for characteristic roofs, monuments and missing features. Record source URL/license/acquisition date and distinguish measurements from estimates and deliberate exaggeration. Recognition depends on references, not just polygon count. For Jonathan's Public Square projects, include the complete square and recognizable surroundings by default, with an editable boundary/palette.

## Verification matched to the object

Inspect intended dimensions and printer fit with practical edge clearance. For CAD check valid solids, positive volume, expected solid count and critical dimensions. For meshes check manifold/watertight status, normals, disconnected shells, intersections, minimum feature thickness and intended body contact. Not every mesh checker detects every defect: state the checks actually performed.

Re-import exports in a clean scene/checker. Compare dimensions and, where meaningful, volume/topology within a documented export tolerance. View top, perspective and close detail. Numeric validity cannot establish that a building looks right or a socket fits a real part.

Open the final project in its compatible slicer when possible. Confirm printer/nozzle, plate, material assignment, scale, orientation, supports, adhesion, separate color bodies and layer preview. Check sliced warnings and purge/support collisions. A command returning success while logging a slicing error is not a pass. A generic CAD 3MF may contain only mesh; configure and save a real slicer project for the final handoff when requested. Never run another machine's embedded G-code merely because its extension matches.

## Handoff and print evidence

Deliver editable source/build script plus useful STEP and labeled STL fallbacks. Prefer a verified multibody slicer 3MF for multicolor handoff when reliable. Include dimensions, material assumption, printer/nozzle, layer height, orientation, supports/adhesion, software versions, known uncertainties and exact validation outcome. Preserve preview images and a file manifest when a release matters.

Software validation is not physical proof. A physically inspected successful print must link to the exact release/profile/settings used. Preserve original error messages/codes, observation evidence and unresolved source matches. Record recommendations separately from facts; do not quietly change settings based on a suggestion. Request or use authorized physical tests where they would resolve important uncertainty.
