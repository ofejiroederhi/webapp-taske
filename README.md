# Task E — Compliance and Supply Chain
SBOM generation for a containerised Flask application, with NIST SSDF compliance mapping.
The detailed report is available here - [`compliance-report.md`](compliance-report.md) 


## Where to find Artefacts

| Title | Directory |
|------|-------|
| Generated SBOM (CycloneDX JSON) | [`sbom/sbom.cdx.json`](sbom/sbom.cdx.json) |
| Dockerfile | [`Dockerfile`](Dockerfile) |
| Python dependencies | [`requirements.txt`](requirements.txt) |
| GitHub Actions pipeline | [`.github/workflows/sbom.yml`](.github/workflows/sbom.yml) |

## Summary
- **Target:** ShopApp Flask webapp (task-d) packaged as a Docker container
- **Tool:** Anchore Syft via `anchore/sbom-action@v0` (GitHub Actions)
- **Format:** CycloneDX JSON — machine-readable, pipeline-parseable, NIST-native
- **Pipeline:** Triggers on every push to `main`; SBOM saved as a named build artifact keyed to the commit SHA

