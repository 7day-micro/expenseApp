"""
Seeder Tool for Expense App Database.
"""

import argparse
import asyncio
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


# Factories


class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session_persistence = None  # We will manually add to session

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
        lambda n: faker.date_between(start_date="-365d", end_date="now")
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
        factories = [UserFactory, CategoryFactory, ExpenseFactory, BudgetFactory]

        for factory_cls in factories:
            factory_cls._meta.sqlalchemy_session = session

        # 1. Generate Users
        users = target_users or UserFactory.build_batch(size=new_users_count)
        session.add_all(users)
        await session.commit()
        print(f"[{len(users)}] Users created and saved.")

        # 2. Setup Categories & Budgets for each user
        user_categories: dict[str, list[Category]] = {}
        all_related_data = []  # collect budgets and categories to bulk insert later

        for user in users:
            # Generate exactly len(CATEGORIES_NAMES) categories per user
            categories = CategoryFactory.build_batch(
                size=len(CATEGORIES_NAMES), user=user
            )
            user_categories[user.uid] = categories
            all_related_data.extend(categories)

            # Generate exactly len(BUDGETS_NAMES) budgets per user
            budgets = [
                BudgetFactory(user=user, category=random.choice(categories))
                for _ in range(len(BUDGETS_NAMES))
            ]
            all_related_data.extend(budgets)

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

        session.add_all(all_expenses)
        await session.commit()

        print(f"[{len(all_expenses)}] Expenses successfully seeded.")

        # Logging
        print(
            f"\n{'=' * 50}\n"
            f"Database Population Summary\n"
            f"{'=' * 50}\n"
            f"  Users:      {len(users)}\n"
            f"  Categories: {len(users) * len(CATEGORIES_NAMES)}\n"
            f"  Budgets:    {len(users) * len(BUDGETS_NAMES)}\n"
            f"  Expenses:   {len(users) * expenses_per_user}\n"
            f"{'=' * 50}\n"
        )


async def populate_single_user(email: str, expenses_per_user: int = 400):
    async with SessionLocal() as session:
        existing_user = await session.execute(select(User).filter(User.email == email))
        existing_user = existing_user.scalar_one_or_none()
        user = None
        if not existing_user:
            UserFactory._meta.sqlalchemy_session = session
            user = UserFactory(email=email)
            session.add(user)
            await session.commit()
            print(f"User with email '{email}' created.")
            # Close session to avoid issues with detached instances
        else:
            user = existing_user
        session.close()

    await populate_users_and_data([user], expenses_per_user=expenses_per_user)


async def populate_existing_users(expenses_per_user: int = 400):
    async with SessionLocal() as session:
        existing_users = await session.execute(session.query(User))
        existing_users = existing_users.scalars().all()

        if not existing_users:
            print(
                """ No existing users found. Please run
                --seed-new-users to create random users\n
                or \n
                --user-email passing an email to create a user."""
            )
            return

        print(f"Found {len(existing_users)} existing users. Populating expenses...")

        await populate_users_and_data(
            target_users=existing_users, expenses_per_user=expenses_per_user
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
