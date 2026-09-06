# Contributing

Contributions from people and agent-assisted workflows are welcome through issues and pull requests. Explain the real printing problem, what changes, and the evidence. Credit human and AI assistance honestly; the submitting person is responsible for reviewing the result. A contributor list is recognition, not a transfer of ownership.

Keep one canonical skill. Put user-specific choices inside its User config block and conditional detail in the relevant reference. Avoid new global restrictions based on one printer, one failure, or one person's taste. Support new tools and methods when they improve outcomes; don't require everyone to install them. Keep instructions agent-neutral and direct, using current official sources for changing technical claims.

Preserve important distinctions: design versus measured geometry, mesh versus configured slicer project, inventory versus loaded state, estimate versus observation, software validation versus physically inspected success. Retain original evidence and private-data boundaries. Do not include keys, credentials, private receipts or third-party assets without permission to redistribute.

For changes, run the packaging/link checks in the testing runbook and validate the skill format; GitHub Actions runs the same packager on every push and pull request. Test executable examples in a supported runtime when changed. For behavior changes, describe a realistic scenario and the resulting agent decision; add automated checks only when they protect a meaningful invariant. A model change should include dimensions, export/round-trip evidence and a preview when relevant. Do not claim physical testing unless someone inspected the exact print.

Keep the core concise; references should earn their context cost. PRs should include purpose, validation, compatibility/update impact and source attribution. Add a changelog entry and your preferred contributor credit. MIT is the inbound and outbound license for contributions; by submitting you confirm you can contribute under it. Maintainers may request changes or decline work based on scope, clarity or evidence.

Maintainer release checklist: review the diff and config, update VERSION/changelog, run verification, build the bundle, verify its contents and checksum, tag the reviewed commit as vVERSION, and upload the ZIP and SHA256SUMS to that GitHub release. Ensure the website download points to that same release. Publishing authority comes from the user's task, not this checklist.
