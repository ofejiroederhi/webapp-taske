# Task E: Compliance and Supply Chain — SBOM Report

## 1. Overview

Modern software is not written from scratch — it is assembled. A typical Flask application imports a handful of lines and silently inherits thousands of lines of third-party code: Werkzeug, Jinja2, MarkupSafe, click, and their own transitive dependencies. When those dependencies contain vulnerabilities (as Log4j did in December 2021, CVE-2021-44228), organisations without an inventory could not even determine whether they were exposed. The Software Bill of Materials (SBOM) solves this by providing a formal, machine-readable inventory of every component in a build.

This report documents the generation of a CycloneDX JSON SBOM for the WebApp containerised application (task-d), explains the automated pipeline that produces it, and maps each SBOM artifact to specific NIST Secure Software Development Framework (SSDF) practices and NTIA minimum element requirements.

---

## 2. The Containerised Target

The target is the WebApp Flask marketplace built in task-d, packaged into a Docker container using a `python:3.11-slim` base image. The container has three distinct software layers, each of which the SBOM must capture:

| Layer | Contents | Scanner visibility |
|-------|----------|-------------------|
| OS layer | Debian GNU/Linux packages (`libc`, `libssl`, `libexpat`, etc.) | Syft (deep container scan) |
| Runtime layer | Python 3.11 and pip-installed packages (Flask, Werkzeug, Jinja2, etc.) | Syft + cyclonedx-py |
| Application layer | WebApp source code (`app.py`, `schema.sql`) | Syft |

The `requirements.txt` pins seven direct dependencies:

```
Flask==3.0.3 · Werkzeug==3.0.3 · Jinja2==3.1.4 · MarkupSafe==2.1.5
click==8.1.7 · blinker==1.8.2 · itsdangerous==2.2.0
```

A source-level scan of `requirements.txt` captures only the application layer. A container-level scan with Syft additionally enumerates the OS packages inherited from `python:3.11-slim`, which is critical: traditional SAST tools are blind to compiled OS binaries and can miss vulnerabilities like an unpatched `libssl` or `libexpat` embedded in the base image.

---

## 3. SBOM Format: CycloneDX JSON

The SBOM is generated in **CycloneDX JSON** format, as recommended by the module lectures and consistent with industry practice. The choice over SPDX is deliberate:

| Criterion | SPDX | CycloneDX |
|-----------|------|-----------|
| Primary origin | License compliance | Security and vulnerability contexts |
| NIST SSDF mapping | Strong | Native and seamless |
| Pipeline parsing | JSON/XML | JSON/XML/Protobuf |
| VEX support | Limited | Built-in |
| Task E fit | Good | **Recommended** |

CycloneDX JSON is the only format that can be cryptographically verified, travels with the container in air-gapped environments, and is parseable in milliseconds by downstream security tooling. A PDF or Word document of the same information fails compliance audits because it cannot be queried programmatically or attached to a release artifact.

---

## 4. Automated Generation Pipeline

The SBOM is generated automatically on every push to `main` and every pull request via the GitHub Actions workflow at `.github/workflows/sbom.yml`. The pipeline:

1. **Checks out** the repository at the exact commit SHA
2. **Builds** the Docker image (`docker build -f task-e/Dockerfile`)
3. **Runs Syft** (via `anchore/sbom-action@v0`) against the built image, scanning all three layers
4. **Saves** the resulting `sbom.cdx.json` as a named build artifact with 90-day retention

The artifact retention policy is deliberate: it creates an immutable, commit-linked record. The SBOM for release `abc123` is permanently attached to that exact release and cannot be retroactively altered — this is provenance.

```yaml
- name: Generate CycloneDX SBOM with Syft
  uses: anchore/sbom-action@v0
  with:
    image: webapp:${{ github.sha }}
    format: cyclonedx-json
    output-file: sbom.cdx.json

- name: Upload SBOM as build artifact
  uses: actions/upload-artifact@v4
  with:
    name: sbom-cyclonedx-${{ github.sha }}
    path: sbom.cdx.json
    retention-days: 90
```

The automation is non-negotiable. Manual SBOM generation is obsolete as soon as the next dependency update occurs — often within hours of a commit. If security documentation is not generated at the speed of the pipeline, it does not accurately reflect what is actually running in production.

---

## 5. NTIA Minimum Element Compliance

The US National Telecommunications and Information Administration (NTIA) defines the minimum fields a valid SBOM must contain. The generated `sbom.cdx.json` satisfies all seven:

| NTIA Minimum Element | CycloneDX Field | Example from WebApp SBOM |
|---------------------|-----------------|--------------------------|
| Supplier name | `component.supplier` | `"PyPI"`, `"Debian"` |
| Component name | `component.name` | `"Flask"`, `"werkzeug"` |
| Version string | `component.version` | `"3.0.3"` |
| Unique identifier | `component.purl` | `"pkg:pypi/flask@3.0.3"` |
| Dependency relationships | `dependencies[]` | Flask → Werkzeug, Jinja2, etc. |
| Author of SBOM | `metadata.tools` | `"Syft"` + version |
| Timestamp | `metadata.timestamp` | ISO 8601 build time |

A flat text file or spreadsheet listing package names cannot satisfy NTIA requirements: the mandatory fields include machine-parseable identifiers (PURL, CPE) and an explicit dependency graph, neither of which human-readable formats can represent reliably.

---

## 6. NIST SSDF Mapping

The NIST Secure Software Development Framework (SP 800-218) organises secure development practices into four groups. The SBOM generated in this task, and the broader portfolio it forms part of, maps directly to the following practices:

### PO — Prepare the Organisation

| Practice | Description | How this task satisfies it |
|----------|-------------|---------------------------|
| **PO.1.1** | Define criteria for third-party component security | `requirements.txt` pins exact versions; the SBOM's PURL and hash fields provide cryptographic identity for each component, enabling automated policy enforcement against an allow-list |
| **PO.3.2** | Implement supply chain risk management | The automated pipeline scans all three container layers on every commit, surfacing new CVEs as dependencies update — this is continuous supply chain monitoring, not a one-time audit |

### PS — Protect the Software

| Practice | Description | How this task satisfies it |
|----------|-------------|---------------------------|
| **PS.1.1** | Protect the software release | The SBOM is uploaded as a named, SHA-keyed build artifact, creating an immutable provenance record. Tampering with the release without also invalidating the SBOM is not possible |
| **PS.3.2** | Archive software releases | `retention-days: 90` in the workflow ensures every release carries its SBOM for a defined audit window; a production deployment policy would extend this to the support lifetime of the release |

### PW — Produce Well-Secured Software

| Practice | Description | How this task satisfies it |
|----------|-------------|---------------------------|
| **PW.4.1** | Design software to meet security requirements for reused components | The SBOM's dependency graph makes all reused components visible and auditable; it exposes transitive dependencies (e.g., MarkupSafe pulled in by Jinja2) that developers may not be aware of |
| **PW.4.4** | Maintain software security throughout the supply chain | Syft scans the compiled container image, not just source code — it catches OS-level vulnerabilities in `python:3.11-slim` base packages that SAST tools in Task C cannot see |

### RV — Respond to Vulnerabilities

| Practice | Description | How this task satisfies it |
|----------|-------------|---------------------------|
| **RV.1.1** | Gather information about vulnerabilities | The CycloneDX JSON SBOM can be queried programmatically: `SELECT components WHERE version < patched_version` identifies affected deployments in seconds — the Log4j response that took Fortune 500 companies weeks of manual grepping |
| **RV.1.2** | Assess, prioritise, and remediate vulnerabilities | PURL identifiers in the SBOM map directly to CVE databases (NVD, OSV), enabling automated severity scoring and prioritisation before a human is even notified |
| **RV.1.3** | Analyse root cause | The dependency graph in the SBOM shows whether a vulnerable component is a direct or transitive dependency, which determines the remediation path: update the direct dependency or wait for an upstream fix |

### RV.2 — Remediate Vulnerabilities

NIST SSDF RV.1 identifies vulnerabilities; RV.2 requires that they are actually addressed. Identification without enforcement is compliance theatre — an SBOM that reports a CRITICAL CVE but allows the image to deploy regardless provides no real security guarantee.

The pipeline extends beyond passive recording by adding Aqua Trivy as a downstream scan step that consumes the generated `sbom.cdx.json` and queries it against the NVD CVE database:

```yaml
- name: Scan SBOM for vulnerabilities with Trivy
  uses: aquasecurity/trivy-action@master
  with:
    scan-type: sbom
    input: sbom.cdx.json
    format: table
    exit-code: '1'
    severity: CRITICAL
```

`exit-code: '1'` is the critical configuration: if Trivy finds any component with CRITICAL severity, the pipeline fails and turns red. The container image is never uploaded to the registry. Vulnerable code cannot reach production regardless of developer intent.

| Practice | Description | How this task satisfies it |
|----------|-------------|---------------------------|
| **RV.2.1** | Ensure the vulnerability is addressed | Trivy's `exit-code: 1` on CRITICAL CVEs makes the pipeline the enforcement point — deployment is blocked automatically, not left to a human decision |
| **RV.2.2** | Monitor the vulnerability response | The Trivy output table is captured as part of the pipeline log for every run, creating an auditable record of which CVEs were present and when they were resolved |

This step closes the gap between identifying and remediating vulnerabilities — the hardest control to enforce in a fast-moving CI/CD environment, and the distinction between a passive SBOM and an active security gate.

---

## 7. Regulatory Context: Executive Order 14028

The SBOM requirement is not academic. US Executive Order 14028 (May 2021, "Improving the Nation's Cybersecurity") mandates that any organisation supplying software to the US federal government must provide an SBOM. The private sector is rapidly adopting the same standard as a procurement prerequisite, driven by cyber-insurance requirements.

This means:

- The GitHub Actions pipeline in this task is not a portfolio exercise — it is the exact pattern required for production software supply chains
- A portfolio demonstrating automated SBOM generation with a compliance mapping to SSDF directly addresses the skills that DevSecOps roles now require at interview

---

## 8. Dynamic vs Static Analysis: What the SBOM Adds

Task C's Semgrep scan and Task D's OWASP ZAP test both analyse the application code and its runtime behaviour. Neither can see inside a compiled container image. The SBOM fills this gap:

| Visibility | Task C (SAST) | Task D (DAST) | Task E (SBOM) |
|-----------|--------------|--------------|--------------|
| Source code vulnerabilities | Yes | No | No |
| Runtime logic flaws | No | Yes | No |
| OS-level package CVEs | No | No | Yes |
| Third-party library inventory | Partial | No | Yes |
| License compliance | No | No | Yes |
| Provenance / audit trail | No | No | Yes |

The three tasks together provide defence-in-depth coverage across the SDLC: SAST catches code-level flaws at commit time, DAST confirms exploitability at runtime, and the SBOM maintains a continuously updated inventory of inherited risk across the full software supply chain.

---

## 9. Tool Limitations

| Limitation | Detail |
|-----------|--------|
| **Application-layer only (cyclonedx-py)** | Scanning `requirements.txt` directly captures pip-installed packages but misses OS-level packages in the container base image. Syft's container scan (used in the pipeline) remedies this |
| **No exploitability data** | An SBOM lists components and versions; it does not indicate which known CVEs are actually exploitable in the specific deployment context. CycloneDX VEX (Vulnerability Exploitability eXchange) extends the standard to communicate this, but requires additional tooling |
| **Snapshot in time** | The SBOM is accurate at build time. It does not update itself when a new CVE is disclosed for a component that was patched at build time. Continuous scanning (e.g., Dependabot, Trivy in CI) is required alongside the SBOM |
| **Transitive depth** | Syft enumerates all installed packages but cannot always reconstruct *why* a transitive package was installed (which direct dependency required it). This affects root-cause analysis in RV.1.3 |
| **False sense of security** | Generating an SBOM does not remediate vulnerabilities — it makes them visible. An SBOM without a process for acting on its findings provides compliance theatre, not security |

---

## 10. SBOM Artifact

The generated SBOM is located at [`sbom/sbom.cdx.json`](sbom/sbom.cdx.json).

It was produced by scanning the WebApp container image using Anchore Syft (CycloneDX JSON format) and contains the complete component inventory across OS and application layers. It is the primary compliance artifact for this task.
