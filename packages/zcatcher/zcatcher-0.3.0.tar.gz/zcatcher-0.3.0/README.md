# zcatcher (sleep tracker)

A simple Python CLI to record sleep entries and view stats.

## Installation

No external dependencies required. Ensure you have Python 3.8+.

Install from source (editable for development):

```bash
python -m pip install -e .
```

This installs the `zcatcher` console command.

Install with pipx (isolated):

```bash
pipx install .
```

If you already installed and pull new changes:

```bash
pipx reinstall zlog
```

## Publish to PyPI

Build and check distributions:

```bash
python3 -m pip install build twine
python3 -m build
python3 -m twine check dist/*
```

Upload using a PyPI token (recommended):

```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD="pypi-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
python3 -m twine upload dist/*
```

Alternatively, configure `~/.pypirc` and omit env vars.

### GitHub Actions (CI Publish)

This repo includes a workflow to publish on GitHub Release:

- Workflow: `.github/workflows/publish.yml`
- Trigger: publishing a GitHub Release or manual `Run workflow`
- Requires a repository secret: `PYPI_API_TOKEN`

Steps to enable:

1. Create a PyPI token with project scope (or scoped to an org). 
2. In your repo, add a secret: `Settings → Secrets and variables → Actions → New repository secret`
  - Name: `PYPI_API_TOKEN`
  - Value: your token (e.g., `pypi-XXXXXXXX...`)
3. Create and publish a GitHub Release for the version (e.g., `v0.3.0`).
  - The workflow builds sdist/wheel and uploads to PyPI.

To use TestPyPI instead, edit the workflow step to set:

```yaml
    - name: Publish to PyPI
      uses: pypa/gh-action-pypi-publish@release/v1
      with:
       password: ${{ secrets.PYPI_API_TOKEN }}
       repository-url: https://test.pypi.org/legacy/
```

## Usage

Record a new entry (interactive prompts):

```bash
zcatcher
```

View stats (all data):

```bash
zcatcher --stats
```

Limit stats to last N days (e.g., 7):

```bash
zcatcher --stats --days 7
```

Output all data as a table:

```bash
zcatcher --data
```

Output all data as JSON:

```bash
zcatcher --json
```

Output all data as CSV to stdout:

```bash
zcatcher --csv
```

Use a custom data file path:

```bash
zcatcher --file /path/to/my_sleep.jsonl --stats
```

## Help

- **Version:** `zcatcher --version` displays the installed version.
- **Interactive entry:** `zcatcher` prompts for sleep time, sleep difficulty, wake time, wake difficulty, and wake date.
- **Stats:** `zcatcher --stats` shows averages; add `--days N` to limit the window.
- **Table:** `zcatcher --data` prints all records in a table (excludes `created_at`).
- **JSON:** `zcatcher --json` prints a JSON array of all records.
- **CSV:** `zcatcher --csv` prints CSV with headers.
- **Custom data path:** `zcatcher --file /path/to/file.jsonl` uses a specific file.

## Data Storage

- Records are stored as JSON Lines in `~/.zcatcher/sleep_data.jsonl` by default (or a custom path via `--file`).
- Each record includes:
  - `sleep_date`, `sleep_time`
  - `wake_date`, `wake_time`
  - `difficulty_sleep` (1-5), `difficulty_wake` (1-5)
  - `duration_hours` (computed)
  - `created_at`

## Notes

- Times can be 24-hour `HH:MM` or `HHMM` (colon optional).
- Prompts now ask in order: sleep time, sleep difficulty, wake time, wake difficulty, then wake date (defaults to today if left blank).
- If the sleep time is later than the wake time (e.g., `23:00` -> `07:00`), the sleep date is assumed to be the previous day.
