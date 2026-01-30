<div align="center">
    <img alt="Betterscan" src="https://cdn.prod.website-files.com/6339e3b81867539b5fe2498d/6662b3cba2059f268d0ada99_cloud%20(Website).svg">
</div>

<h1 align="center">
  Betterscan: The Open DevSecOps Orchestration Toolchain
</h1>

Betterscan (Self hosted and SaaS platform with CLI and Web based interface) used checkmate5 to orchestrate, unify and de-duplicate SAST and scanning tools.

# Checkmate5

![Logo](docs/images/sample-run.png)

Python-based meta static-analysis runner that orchestrates multiple language analyzers (Bandit, tfsec, Brakeman, Kubescape, OpenGrep, Staticcheck, etc.) and stores findings in a database backend.

## Table of Contents
* [Fork notice & acknowledgements](#fork-notice--acknowledgements)
* [About](#about)
* [Licenses](#licenses)
* [Requirements](#requirements)
* [Tools used](#tools-used)
* [CLI usage](#cli-usage)
* [Backend configuration](#backend-configuration)

---

## Fork notice & acknowledgements

This project is a modified version of the original **Checkmate**.

- Original project: <https://github.com/quantifiedcode/checkmate>

---

## About

**Checkmate5** is a cross-language (meta-)tool for static code analysis, written in Python. It orchestrates multiple scanners, normalizes findings into a single view, and de-duplicates overlapping results. This provides a **global overview** of code quality and security findings across a project—aiming to present clear, actionable insights.

Snapshots let you view findings at a specific point in time, while the issues view can also show the full history of findings across all scans for a project.

---

## Licenses

- The original Checkmate project is licensed under the **MIT license**: <https://opensource.org/licenses/MIT>
- Original Checkmate parts remain released under the **MIT License**.
- **This fork’s modifications are released under the AGPL-3.0 license** (previously LGPL 2.1 with Commons Clause). See `LICENSE` for details.

---

## Requirements

- Python **3.8+**
- Python dependencies (typical): `blitzdb5`, `pyyaml`, `sqlalchemy`, `requests`
- **OpenGrep CLI** (local binary) for OpenGrep-based analyzers

## Tools used

Checkmate5 orchestrates external tools. Availability, licensing, and usage terms are governed by each upstream project.

- OpenGrep
- Bandit
- Brakeman
- tfsec
- Kubescape
- Staticcheck

## OpenGrep setup

Checkmate5 uses the local OpenGrep CLI for `opengrep` (generic).

Install OpenGrep (recommended):

```
curl -fsSL https://raw.githubusercontent.com/opengrep/opengrep/main/install.sh | bash
```

The CLI is expected at `~/.opengrep/cli/latest/opengrep` or via `OPENGREP_BIN`.

It will be instaled when missing.

### Rules

Rules are downloaded automatically from:
- <https://github.com/opengrep/opengrep-rules>
- <https://github.com/AikidoSec/opengrep-rules>
- <https://github.com/amplify-security/opengrep-rules>

If rules download fails, OpenGrep falls back to built-in packs.

### Config overrides

- `CHECKMATE_OPENGREP_CONFIG`

### Debugging tool output

Run:

```
checkmate analyze --debug-tools
```

This prints the OpenGrep command, config paths, and raw JSON results.

### Issues output formats

Generate reports from the latest snapshot:

```
checkmate issues --html-output
checkmate issues --json-output
checkmate issues --sarif-output
```

Legacy aliases still work:

```
checkmate issues html
checkmate issues json
checkmate issues sarif
```

## CLI usage

Common flows:

```
checkmate init
checkmate analyze
checkmate issues
```

If you use the git plugin:

```
checkmate git init
checkmate analyze
checkmate issues
```

List snapshots and filter issues to a specific snapshot:

```
checkmate snapshots
checkmate issues --snapshot <snapshot_id_or_prefix>
```

### checkmate init examples

Default (SQLite in `.checkmate/database.db`):

```
checkmate init
```

PostgreSQL:

```
checkmate init --backend sql --connection-string "postgresql+psycopg2://user:password@localhost:5432/checkmate"
```

MySQL:

```
checkmate init --backend sql --connection-string "mysql+pymysql://user:password@localhost:3306/checkmate"
```

Custom SQLite path:

```
checkmate init --backend sqlite --connection-string "sqlite:////absolute/path/to/my-checkmate.db"
```

## Backend configuration

Projects are configured in `.checkmate/config.json`. A typical sqlite setup looks like:

```
{
  "project_id": "YOUR_PROJECT_ID",
  "project_class": "Project",
  "backend": {
    "driver": "sqlite",
    "connection_string": "sqlite:////absolute/path/to/.checkmate/database.db"
  }
}
```

PostgreSQL example:

```
{
  "project_id": "YOUR_PROJECT_ID",
  "project_class": "Project",
  "backend": {
    "driver": "sql",
    "connection_string": "postgresql+psycopg2://user:password@localhost:5432/checkmate"
  }
}
```

MySQL example:

```
{
  "project_id": "YOUR_PROJECT_ID",
  "project_class": "Project",
  "backend": {
    "driver": "sql",
    "connection_string": "mysql+pymysql://user:password@localhost:3306/checkmate"
  }
}
```

Notes:

- For PostgreSQL, install `psycopg2` (or `psycopg`).
- For MySQL, install `pymysql`.
- For SQLite, the file will be created if it does not exist.