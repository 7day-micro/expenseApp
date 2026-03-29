## 🛠️ Development Setup

### 1. Install Dependencies

Choose your preferred package manager:

#### Using uv (Recommended)

``` bash
uv sync
```

#### Using pip

``` bash
pip install -r requirements.txt
```

------------------------------------------------------------------------

### 2. Enable Git Hooks (pre-commit)

Hooks automatically run linting and formatting checks before each commit
to ensure code quality.

#### Using uv

``` bash
uv run pre-commit install
```

#### Using standard Python

``` bash
pre-commit install
```

------------------------------------------------------------------------

## Usage

### Automatic Checks

Once installed, pre-commit runs automatically on every git commit.

If issues are found: - They may be fixed automatically, or - The commit
will be blocked for manual fixes

⚠️ Note: If files are automatically fixed, the commit will fail. You need to review the changes, stage them again, and re-run the commit.

------------------------------------------------------------------------

### Manual Execution

To run all checks across all files at any time:

``` bash
uv run pre-commit run --all-files
```

``` bash
# or
pre-commit run --all-files
```