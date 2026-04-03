# 💸 ExpenseApp

A FastAPI-powered expense tracking API that helps users manage their finances by tracking expenses, setting budgets, and organising spending by category.

---

## 📋 Table of Contents

- [Development Setup](`#development-setup`)
- [Database Setup](`#database-setup`)
- [Migrations] (``)
- [Running the App](#-running-the-app)
- [Testing](#-testing)
- [Code Quality](#-code-quality)

---

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

### 2. Set Up Environment Variables

Copy the example below into a `.env` file at the root of the project:

```shell
# DEV SETUP
DATABASE_HOSTNAME=localhost
DATABASE_PORT=5432
DATABASE_PASSWORD=admin
DATABASE_NAME=expense_db
DATABASE_USERNAME=admin
SECRET_KEY=uma_chave_muito_longa_e_aleatoria
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 3. Enable Git Hooks (pre-commit)

Hooks automatically run linting and formatting checks before each commit to ensure code quality.

#### Using uv

```bash
uv run pre-commit install
```

#### Using standard Python

```bash
pre-commit install
```

---

## 🗄️ Database Setup

### Using Docker (Recommended)

1. Ensure Docker is installed on your machine
2. Start the database container:

```bash
docker compose up -d
```

---

## Migrations (Alembic)
1. Create a new migration after making changes to your SQLAlchemy models:
```bash
uv run alembic revision --autogenerate -m "describe your change here"
```

2. Apply migrations (upgrade to head):
```bash
uv run alembic upgrade head
```

### Other useful commands
```bash
# Check current migration version applied to the DB
uv run alembic current

# See migration history
uv run alembic history

# Roll back one migration
uv run alembic downgrade -1
```
## 🚀 Running the App

### Mac/Linux

```bash
uv run uvicorn src.main:app --reload
```

### ⚠️ Windows Users

`uvloop` does not support Windows. Use the following command instead:

```bash
uv run uvicorn src.main:app --loop asyncio --reload
```

Once running, visit:

- **API:** http://127.0.0.1:8000
- **Interactive Docs (Swagger):** http://127.0.0.1:8000/docs
- **Alternative Docs (ReDoc):** http://127.0.0.1:8000/redoc

---

## 🧪 Testing

The `./conftest.py` file contains utility fixtures available across all tests.

To run tests and verify your changes don't break the app:

```bash
uv run pytest
```

> ⚠️ Run tests on every new feature or change before opening a PR.

---

## ✅ Code Quality

### Automatic Checks

Once pre-commit is installed, it runs automatically on every `git commit`.

If issues are found:

- They may be **fixed automatically**, or
- The commit will be **blocked** for manual fixes

> ⚠️ If files are automatically fixed, the commit will fail. Review the changes, stage them again, and re-run the commit.

### Manual Execution

To run all checks across all files at any time:

```bash
uv run pre-commit run --all-files
```
