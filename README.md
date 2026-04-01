## API Setup

### 1 - Set .env file

Make sure all settings that this app need is setted on .env file
bellow and example to quick run the project

```shell
#DEV SET
ENV=DEV
DATABASE_HOSTNAME=localhost
DATABASE_PORT=5432
DATABASE_PASSWORD=admin
DATABASE_NAME=expense_db
DATABASE_USERNAME=admin
SECRET_KEY=uma_chave_muito_longa_e_aleatoria
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

```

### 3 - Initialize database

- see database setup section

### 2 - Start up FastAPI app

```shell
run uv run uvicorn src.main:app --reload
```

## 🛠️ Database Setup

### 1 Ensure docker installed

### 2 initialize container

```shell
docker compose up -d
```

## 🛠️ Development Setup

### 1. Install Dependencies

Choose your preferred package manager:

#### Using uv (Recommended)

```bash
uv sync
```

#### Using pip

```bash
pip install -r requirements.txt
```

---

### 2. Enable Git Hooks (pre-commit)

Hooks automatically run linting and formatting checks before each commit
to ensure code quality.

#### Using uv

```bash
uv run pre-commit install
```

#### Using standard Python

```bash
pre-commit install
```

---

## Usage

### Automatic Checks

Once installed, pre-commit runs automatically on every git commit.

If issues are found: - They may be fixed automatically, or - The commit
will be blocked for manual fixes

⚠️ Note: If files are automatically fixed, the commit will fail. You need to review the changes, stage them again, and re-run the commit.

---

### Manual Execution

To run all checks across all files at any time:

```bash
uv run pre-commit run --all-files
```

```bash
# or
pre-commit run --all-files
```

### Migrations (Alembic)

Create new migration, after making changes to you models

```shell
uv run alembic revision --autogenerate -m "describe your change here"
```

Apply Migrations

```shell
uv run alembic upgrade head
```

Other useful commands

```shell
# Check current migration version applied to the DB
uv run alembic current

# See migration history
uv run alembic history

# Roll back one migration
uv run alembic downgrade -1
```

### Tests

```shell
#TEST SETUP
ENV=TEST
TEST_DATABASE_HOSTNAME=localhost
TEST_DATABASE_PORT=5432
TEST_DATABASE_PASSWORD=admin
TEST_DATABASE_NAME=test_expense_db
TEST_DATABASE_USERNAME=admin
```

#### How to test the app

In the `./conftest.py` file there are utils fixtures to be used on all test through the project

#### How to run test

To be sure your changes will not broke the app, run test on every new feature added/ changes

- Run `uv run pytest`
