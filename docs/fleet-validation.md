# Run the package and CAD checks on Fleet

The `cad-ci` suite runs the existing compile, full dependency import, complete
unit suite and package command on the exact pull request head/base. The image
contains every dependency in `tests/requirements-cad.txt`, so the CAD verifier
coverage is present on every run. The duplicate full test invocation from the
second Actions job is consolidated; no test or assertion is removed.

Ask Mini 2's Fleet broker through the message board with exactly:

```json
{"suite":"cad-ci","pr":1}
```

Replace `1` with the open PR number. Only same-repository PRs from a trusted
writer are eligible; forks and untrusted contributors do not execute on Fleet.
The broker has an explicit owned-public allowlist entry for this repository.
PR code receives no GitHub token, Vault enrollment, host home or Docker socket.

Hosted package coverage remains active until the whole replacement and its
separate failure control are proven on this changeover PR.
