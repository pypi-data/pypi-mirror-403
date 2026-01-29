CIRM ODMs

**CIRM ODMs** is a Python package developed by **CyberSecurity S.r.l.** to centralize and validate data models used in the **CIRM** project — a framework for managing cyber risk, with a specific focus on software vulnerability management.

This package contains all the **Object Document Mappers (ODMs)** built with [Pydantic](https://docs.pydantic.dev/) and Beanie, designed to work with [MongoDB](https://www.mongodb.com/) and ensure reliable, strongly-typed data validation.

The goal is to support internal use within the CIRM ecosystem, while also making the models publicly available for reuse in other CyberSecurity-related projects.

---

## Project Context

The **CIRM** (Continuous Improvement Risk Management) platform automates the handling of software vulnerabilities by integrating:

- **Official data sources** such as the [National Vulnerability Database (NVD)](https://nvd.nist.gov/), which provides CVE records, CWE categorizations, and CPE identifiers.
- **AI models** for automatically predicting important parameters, such as:
  - CVSS scores (vulnerability severity),
  - CWE classes (weakness types),
  - Affected CPEs (platforms or software).

The extracted and predicted data is stored in a **MongoDB** database and validated through the Pydantic/Beanie models provided in this package.

---

## Package Features

- ODMs for CVE, CWE, and CPE entities
- MongoDB-compatible schemas
- Automatic data validation
- Modern packaging with `pyproject.toml` and [Flit](https://flit.pypa.io/)

---

## Technology Stack

- **Python**
- **Pydantic** / **Beanie**
- **Flit** for packaging and publishing
- Central configuration via **pyproject.toml**

---

## Project Structure

```txt
.
├── .github/workflows/         # GitHub Actions for build & publish
├── .devcontainer/             # VSCode DevContainer setup
│   ├── Dockerfile
│   └── devcontainer.json
├── .vscode/settings.json      # Project-specific VSCode settings
├── src/                       # Source code of the package
├── tests/                     # Unit tests for ODMs
├── pyproject.toml             # Project metadata and config
└── README.md                  # Project documentation
```

## Installation

Once published to PyPI:

```bash
pip install cirm-odm
```
