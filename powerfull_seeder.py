import argparse
import asyncio
import datetime
import random

import factory
from faker import Faker
from sqlalchemy import select

from src.auth.oauth2 import get_password_hash
from src.db import SessionLocal
from src.models import Budget, Category, Expense, User

# -----------------------------------------------------------------------------
# CLI Configuration
# -----------------------------------------------------------------------------
parser = argparse.ArgumentParser(
    description="Seed Expense App database with users, categories, budgets, and expenses.",
    formatter_class=argparse.RawTextHelpFormatter,
    epilog=(
        "Examples:\n"
        "  python powerfull_seeder.py --seed-new-users --new-users-count 10 --expenses-per-user 250\n"
        "  python powerfull_seeder.py --user-email user@example.com --expenses-per-user 120\n"
        "  python powerfull_seeder.py --seed-existing-users --expenses-per-user 500"
    ),
)

mode_group = parser.add_mutually_exclusive_group(required=True)
mode_group.add_argument(
    "--user-email",
    "--email",
    dest="user_email",
    type=str,
    help="Populate data for a specific user email. Creates the user if it does not exist.",
)
mode_group.add_argument(
    "--seed-new-users",
    "--create-and-populate",
    "--create_and_populate",
    dest="seed_new_users",
    action="store_true",
    help="Create random users, then populate related data for each one.",
)
mode_group.add_argument(
    "--seed-existing-users",
    "--existing-users",
    "--existent-users",
    dest="seed_existing_users",
    action="store_true",
    help="Populate data for users already present in the database.",
)

parser.add_argument(
    "--new-users-count",
    "--users-count",
    type=int,
    default=8,
    help="Number of users to create when using --seed-new-users (default: 8).",
)
parser.add_argument(
    "--expenses-per-user",
    type=int,
    default=400,
    help="Number of expenses generated per user (default: 400).",
)

# -----------------------------------------------------------------------------
# Constants & Setup
# -----------------------------------------------------------------------------
faker = Faker()

DEFAULT_PASSWORD_HASH = get_password_hash("Valid2026#")

CATEGORIES_NAMES = [
    "sports",
    "rent",
    "school",
    "netflix",
    "groceries",
    "travel",
    "utilities",
]
BUDGETS_NAMES = [
    "food",
    "entertainment",
    "transportation",
    "health",
    "education",
    "shopping",
    "other",
]

# -----------------------------------------------------------------------------
# Factories
# -----------------------------------------------------------------------------


class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session_persistence = None

    username = factory.Sequence(lambda n: faker.unique.user_name())
    email = factory.Sequence(lambda n: faker.unique.email())
    password_hash = DEFAULT_PASSWORD_HASH


class CategoryFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Category
        sqlalchemy_session_persistence = None

    name = factory.Iterator(CATEGORIES_NAMES)
    color_icon = factory.Sequence(lambda n: faker.color_name())


class ExpenseFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Expense
        sqlalchemy_session_persistence = None

    amount = factory.Sequence(lambda n: faker.pyfloat(min_value=3, max_value=120))
    note = factory.Sequence(lambda n: faker.sentence(20))
    transaction_date = factory.Sequence(
        lambda n: faker.date_time_between(
            start_date="-365d",
            end_date="now",
            tzinfo=datetime.UTC,  # <- A mágica acontece aqui
        )
    )


class BudgetFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Budget
        sqlalchemy_session_persistence = None

    name = factory.Iterator(BUDGETS_NAMES)
    amount_limit = factory.Sequence(
        lambda n: faker.pyfloat(min_value=500, max_value=3000)
    )
    month_year = factory.Sequence(
        lambda n: faker.date_between(start_date="-365d", end_date="+30d")
    )


# -----------------------------------------------------------------------------
# Core Seeding Logic
# -----------------------------------------------------------------------------
async def populate_users_and_data(
    target_users: list[User] | None = None,
    new_users_count: int = 8,
    expenses_per_user: int = 400,
):
    async with SessionLocal() as session:
        # 1. Setup / Merge Users
        if target_users:
            # Target users are likely detached; merge them safely into the new session.
            users = [await session.merge(u) for u in target_users]
        else:
            users = UserFactory.build_batch(size=new_users_count)
            session.add_all(users)
            await session.commit()
            print(f"[{len(users)}] Users created and saved.")

        # 2. Setup Categories & Budgets for each user
        user_categories: dict[str, list[Category]] = {}
        all_related_data = []

        for user in users:
            # Manual Async Get-Or-Create for Categories to respect UniqueConstraints
            existing_cats_req = await session.execute(
                select(Category).where(Category.user_id == user.uid)
            )
            existing_cats = {c.name: c for c in existing_cats_req.scalars().all()}

            categories = [
                None,
            ]
            for name in CATEGORIES_NAMES:
                if name in existing_cats:
                    categories.append(existing_cats[name])
                else:
                    new_cat = CategoryFactory.build(user=user, name=name)
                    all_related_data.append(new_cat)
                    categories.append(new_cat)

            user_categories[user.uid] = categories

            # Manual Async Get-Or-Create for Budgets
            existing_budgets_req = await session.execute(
                select(Budget).where(Budget.user_id == user.uid)
            )
            existing_budgets = {b.name: b for b in existing_budgets_req.scalars().all()}

            for name in BUDGETS_NAMES:
                if name not in existing_budgets:
                    new_budget = BudgetFactory.build(
                        user=user, name=name, category=random.choice(categories)
                    )
                    all_related_data.append(new_budget)

        if all_related_data:
            session.add_all(all_related_data)
            await session.commit()
        print("Categories and Budgets initialized for all users.")

        # 3. Generate Expenses in Bulk
        all_expenses = []
        for user in users:
            categories_for_this_user = user_categories[user.uid]

            expenses = ExpenseFactory.build_batch(
                size=expenses_per_user,
                user=user,
                category=factory.LazyFunction(
                    lambda categories=categories_for_this_user: random.choice(
                        categories
                    )
                ),
            )
            all_expenses.extend(expenses)

            # Bulk insert in batches to avoid memory issues
            if len(all_expenses) > 5000:
                session.add_all(all_expenses)
                await session.commit()
                all_expenses.clear()

        if all_expenses:
            session.add_all(all_expenses)
            await session.commit()

        print(f"[{len(users) * expenses_per_user}] Expenses successfully seeded.")


async def populate_single_user(email: str, expenses_per_user: int = 400):
    async with SessionLocal() as session:
        existing_user_result = await session.execute(
            select(User).filter(User.email == email)
        )
        user = existing_user_result.scalar_one_or_none()

        if not user:
            # Just build locally, let session.add() manage the rest
            user = UserFactory.build(email=email)
            session.add(user)
            await session.commit()
            print(f"User with email '{email}' created.")
        else:
            print(f"User with email '{email}' already exists.")

    # The session cleans itself up via `async with` context manager.
    await populate_users_and_data([user], expenses_per_user=expenses_per_user)


async def populate_existing_users(expenses_per_user: int = 400):
    async with SessionLocal() as session:
        # Avoid `session.query` with AsyncSession. Replaced with `select`
        existing_users_result = await session.execute(select(User))
        existing_users = existing_users_result.scalars().all()

        if not existing_users:
            print("No existing users found. Please run --seed-new-users")
            return

        print(f"Found {len(existing_users)} existing users. Populating expenses...")

    # existing_users are technically detached here but populate_users_and_data properly re-merges them
    await populate_users_and_data(
        target_users=list(existing_users), expenses_per_user=expenses_per_user
    )


if __name__ == "__main__":
    args = parser.parse_args()

    print(f"Arguments received: {args}")

    if args.seed_new_users:
        asyncio.run(
            populate_users_and_data(
                new_users_count=args.new_users_count,
                expenses_per_user=args.expenses_per_user,
            )
        )
    elif args.user_email:
        asyncio.run(
            populate_single_user(
                email=args.user_email, expenses_per_user=args.expenses_per_user
            )
        )
    elif args.seed_existing_users:
        asyncio.run(populate_existing_users(expenses_per_user=args.expenses_per_user))
    else:
        parser.print_help()
