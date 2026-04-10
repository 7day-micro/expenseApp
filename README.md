# 💸 ExpenseApp

A FastAPI-powered expense tracking API that helps users manage their finances by tracking expenses, setting budgets, and organising spending by category.

---

## 📋 Table of Contents

- [Development Setup](`#development-setup`)
- [Database Setup](`#database-setup`)
- [Database Migrations](#database-migrations)
- [Database Seeder](#database-seeder)
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

## Database Migrations

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

## Database Seeder

Use `powerfull_seeder.py` to generate realistic test data for users, categories, budgets, and expenses.

Before running the seeder:

1. Make sure the database container is running.
2. Make sure migrations are applied (`uv run alembic upgrade head`).

> PASSWORD FOR ALL GENERATED USERS IS : `Valid2026#`

### Available modes (choose one)

- `--seed-new-users`: creates random users and related data.
- `--seed-existing-users`: adds related data for users already in the database.
- `--user-email`: seeds data for one specific user email (creates the user if it does not exist).

### Useful options

- `--new-users-count` (default: `8`): number of users created with `--seed-new-users`.
- `--expenses-per-user` (default: `400`): number of expenses generated for each user.

### Examples

```bash
# Create 8 random users (default) and seed 400 expenses per user (default)
uv run python powerfull_seeder.py --seed-new-users

# Create 10 users and 250 expenses per user
uv run python powerfull_seeder.py --seed-new-users --new-users-count 10 --expenses-per-user 250

# Seed one specific user
uv run python powerfull_seeder.py --user-email user@example.com --expenses-per-user 120

# Seed all existing users
uv run python powerfull_seeder.py --seed-existing-users --expenses-per-user 500
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
