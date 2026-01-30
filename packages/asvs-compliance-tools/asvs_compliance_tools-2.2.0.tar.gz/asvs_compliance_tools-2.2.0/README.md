<div align="center">

# ASVS Compliance Engine

### Turn Security Requirements into Verifiable Code.

[![CircleCI](https://dl.circleci.com/status-badge/img/gh/Kaademos/asvs-compliance-starter-kit/tree/main.svg?style=shield)](https://dl.circleci.com/status-badge/redirect/gh/Kaademos/asvs-compliance-starter-kit/tree/main)
[![PyPI - Version](https://img.shields.io/pypi/v/asvs-compliance-tools?style=flat-square&color=0066FF&labelColor=1c1c1c)](https://pypi.org/project/asvs-compliance-tools/)
[![Python Version](https://img.shields.io/pypi/pyversions/asvs-compliance-tools?style=flat-square&color=0066FF&labelColor=1c1c1c)](https://pypi.org/project/asvs-compliance-tools/)
[![License](https://img.shields.io/badge/license-Apache_2.0-0066FF?style=flat-square&labelColor=1c1c1c)](LICENSE)
[![Docker](https://img.shields.io/badge/docker-ready-0066FF?style=flat-square&labelColor=1c1c1c&logo=docker)](Dockerfile)

<br/>

<img src="https://placehold.co/1200x600/1c1c1c/0066FF?text=Video+Placeholder:+10s+Terminal+Workflow+Demo&font=montserrat" alt="ASVS Compliance Engine Demo" width="100%" />

<br/>
<br/>

**Stop managing security in spreadsheets.**
The ASVS Compliance Engine is a DevSecOps toolkit that operationalizes the **OWASP Application Security Verification Standard (ASVS) 5.0**. It treats compliance as code, scanning your infrastructure, verifying your app headers, and enforcing evidence requirements in your CI/CD pipeline.

[**Get Started**](#-quick-start) · [**Documentation**](docs/) · [**Report Bug**](https://github.com/kaademos/asvs-compliance-starter-kit/issues)

</div>

---

## ⚡ The Problem: Compliance Rot

Most security compliance efforts fail because they rely on static documents (Word/Excel) that become obsolete the moment they are written. This engine bridges the gap between **Requirements** and **Reality**.

| ❌ The Old Way (Static) | ✅ The Compliance Engine (Dynamic) |
| :--- | :--- |
| **Manual Attestation:** "I promise we use bcrypt." | **Automated Evidence:** Scans `package.json` for `bcrypt` library. |
| **Stale Docs:** Architecture diagrams from 2021. | **Living Docs:** Requirements mapped directly to code files. |
| **Blind Spots:** Cloud configs checked manually. | **IaC Scanning:** Terraform plans scanned for ASVS V5.3 violations. |
| **Audit Panic:** Scrambling for screenshots. | **Instant Dashboards:** Single-click HTML audit reports. |

---

## 🚀 Key Features

### 1. Automated Evidence Verification
Don't just claim you use secure libraries—prove it. Map ASVS requirements directly to files in your repository using `evidence.yml`. The engine verifies their existence and content during every build.

<img src="https://placehold.co/1000x400/1c1c1c/0066FF?text=Image+Placeholder:+Evidence.yml+Configuration+vs+Terminal+Success&font=montserrat" alt="Evidence Verification" width="100%" />

### 2. Infrastructure-as-Code (IaC) Scanning
Shift security left by catching cloud storage misconfigurations before they deploy. Our native scanner checks Terraform plans against **ASVS V5.3** (Storage & Cryptography).

<img src="https://placehold.co/1000x300/1c1c1c/0066FF?text=Image+Placeholder:+Terminal+showing+S3+Encryption+Failure&font=montserrat" alt="IaC Scanner" width="100%" />

### 3. Auditor-Ready Dashboards
Stop manually compiling evidence. Generate a comprehensive HTML report that combines documentation status, code evidence, and DAST results into a single pane of glass for your SOC2/ISO 27001 auditor.

<img src="https://placehold.co/1000x500/1c1c1c/0066FF?text=Image+Placeholder:+Auditor+Dashboard+Screenshot&font=montserrat" alt="Compliance Dashboard" width="100%" />

---

## 🛠️ Quick Start

### Option A: Python (Recommended)

```bash
# 1. Install the toolkit
pip install "asvs-compliance-tools[evidence,verification]"

# 2. Initialize your project (Interactive Wizard)
# Generates your security docs and evidence.yml
python -m tools.init_project --interactive

# 3. Verify Compliance
# Scans your docs and code for evidence
python -m tools.compliance_gate --level 2 --evidence-manifest evidence.yml
```

### Option B: Docker

No Python environment? No problem.

```bash
# Build the image
docker build -t asvs-engine .

# Run the Compliance Gate
docker run -v $(pwd):/app asvs-engine tools.compliance_gate --level 2
```

---

## 📦 What's Inside?

| Tool | Command | Description |
| --- | --- | --- |
| **Compliance Gate** | `compliance_gate` | Enforces documentation and code evidence rules. |
| **Verification Suite** | `verification_suite` | DAST scanner for Security Headers, CSRF, and Cookies. |
| **IaC Scanner** | `iac_scanner` | Scans Terraform plans for unencrypted storage. |
| **Drift Detector** | `drift_detector` | Checks if your ASVS definitions are out of sync with OWASP. |
| **Report Gen** | `generate_report` | Compiles JSON outputs into an HTML dashboard. |

---

## 🤝 Contributing

We are building the standard for open-source compliance.

* **[Roadmap](ROADMAP.md):** See our plans for Jira Sync and VS Code extensions.
* **[Contributing Guide](CONTRIBUTING.md):** How to set up your dev environment.

## 💖 Support the Project

If this tool saves your team hours of audit preparation, please consider [sponsoring the development](.github/FUNDING.yml). Your support funds the creation of pre-built Evidence Packs for frameworks like **Django**, **Spring Boot**, and **Node.js**.

---

<div align="center">
<sub>Built with ❤️ for the Security Community</sub>
</div>

<p align="center">
  <a href="https://owasp.org/www-project-application-security-verification-standard/">OWASP ASVS</a> •
</p>
