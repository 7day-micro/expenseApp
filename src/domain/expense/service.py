import datetime
from decimal import Decimal
from math import ceil
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload

from src.common.base_service import BaseService
from src.domain.category.service import CategoryService
from src.domain.expense.schemas import (
    ExpenseCreateSchema,
    ExpenseSchema,
    ExpenseUpdateSchema,
    MetaSchema,
    PaginatedResponseSchema,
)
from src.exceptions import DatabaseException, EntityNotFoundException
from src.models import Expense


class ExpenseService(
    BaseService[Expense, ExpenseCreateSchema, ExpenseSchema, ExpenseUpdateSchema]
):
    async def create(self, data: ExpenseCreateSchema, user_id: UUID) -> Expense:

        """
        Create a new Expense for the specified user and return the persisted Expense with its category relationship loaded.
        
        Parameters:
            data (ExpenseCreateSchema): Fields for the new expense; `user_id` from the schema is ignored and replaced by the provided `user_id`.
            user_id (UUID): UUID of the owner to associate with the created expense.
        
        Returns:
            Expense: The created Expense instance reloaded from the database with its `category` relationship eagerly loaded.
        
        Raises:
            DatabaseException: If a database error occurs while committing the new expense.
            EntityNotFoundException: If the referenced category (when provided) does not exist for the given `user_id`, or if the created expense cannot be found when reloading.
        """
        if data.category_id is not None:
            category_service = CategoryService(self.db)
            await category_service.get_by_id(data.category_id, user_id)

        expense = Expense(**data.model_dump(exclude={"user_id"}))
        expense.user_id = user_id

        self.db.add(expense)
        try:
            await self.db.commit()
            await self.db.refresh(expense)
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise DatabaseException(
                operation="creating",
                entity_name="Expense",
                details={"user_id": str(user_id), "original_error": str(e)},
            ) from e

        return await self.get_by_id(object_id=expense.id, user_id=user_id)

    async def update(
        self, object_id: Any, data: ExpenseUpdateSchema, user_id: UUID
    ) -> Expense:
        """
        Update fields of an existing Expense owned by the given user and return the refreshed instance with its category relationship loaded.
        
        Parameters:
            object_id (Any): Identifier of the Expense to update.
            data (ExpenseUpdateSchema): Partial update values; `category_id` may be explicitly set to `None`.
            user_id (UUID): Owner's user ID used to scope and validate the Expense and category.
        
        Returns:
            Expense: The updated Expense instance with its `category` relationship eagerly loaded.
        
        Raises:
            DatabaseException: If committing or refreshing the updated Expense fails.
        """
        expense = await self.get_by_id(object_id, user_id)

        # Since exclude_none will ignore all fields
        # and sometimes we want get category_id set to None
        # The use of exclude_none here is not suitable
        # So we need to manually loop through the fields and set
        # them if they are not None (except for category_id which can be set to None)
        if data.category_id:
            await CategoryService(self.db).get_by_id(data.category_id, user_id=user_id)

        for key, value in data.model_dump(
            exclude={"user_id"}, exclude_unset=True
        ).items():
            # Ensure only category_id can be set to None, other fields will be ignored if None
            if key == "category_id" and value is None:
                expense.category_id = value
            elif value is not None:
                setattr(expense, key, value)

        try:
            await self.db.commit()
            await self.db.refresh(expense)
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise DatabaseException(
                operation="updating",
                entity_name="Expense",
                details={
                    "object_id": object_id,
                    "user_id": str(user_id),
                    "original_error": str(e),
                },
            ) from e

        stmt = (
            select(Expense)
            .options(selectinload(Expense.category))
            .where(Expense.id == expense.id)
        )

        result = await self.db.execute(stmt)

        return result.scalar_one()

    async def delete(self, object_id: Any, user_id: UUID) -> None:
        expense = await self.get_by_id(object_id, user_id)

        try:
            await self.db.delete(expense)
            await self.db.commit()

        except SQLAlchemyError as e:
            await self.db.rollback()
            raise DatabaseException(
                operation="deleting",
                entity_name="Expense",
                details={
                    "object_id": object_id,
                    "user_id": str(user_id),
                    "original_error": str(e),
                },
            ) from e

    async def get_by_id(self, object_id: Any, user_id: UUID) -> Expense:
        statement = (
            select(Expense)
            .options(selectinload(Expense.category))
            .where(Expense.id == object_id, Expense.user_id == user_id)
        )
        result = await self.db.execute(statement)
        expense = result.scalar_one_or_none()

        if not expense:
            raise EntityNotFoundException(entity_name="Expense", object_id=object_id)

        return expense

    async def get_all(
        self,
        user_id: UUID,
        page: int = 1,
        limit: int = 20,
        date_filter: datetime.date | None = None,
        start_date: datetime.date | None = None,
        end_date: datetime.date | None = None,
        min_value: Decimal | None = None,
        max_value: Decimal | None = None,
    ) -> PaginatedResponseSchema:
        """
        Retrieve a paginated list of expenses for a given user, optionally filtered by exact date, date range, and amount bounds.
        
        Parameters:
            user_id (UUID): Owner of the expenses to retrieve.
            page (int): 1-based page number; values less than 1 are treated as 1.
            limit (int): Maximum items per page; values above 50 are capped to 50.
            date_filter (datetime.date | None): If provided, include only expenses whose transaction_date equals this date.
            start_date (datetime.date | None): If provided and `date_filter` is None, include expenses with transaction_date on or after this date.
            end_date (datetime.date | None): If provided and `date_filter` is None, include expenses with transaction_date on or before this date.
            min_value (Decimal | None): If provided, include expenses with amount greater than or equal to max(0, min_value).
            max_value (Decimal | None): If provided, include expenses with amount less than or equal to max(0, max_value).
        
        Returns:
            PaginatedResponseSchema: Contains `data`, a list of Expense instances (each with its `category` eagerly loaded), and `meta` with pagination info (`total`, `count`, `page`, `total_pages`).
        """
        statement = (
            select(Expense)
            .options(selectinload(Expense.category))
            .where(Expense.user_id == user_id)
        )

        if date_filter is not None:
            statement = statement.where(
                func.date(Expense.transaction_date) == date_filter
            )
        else:
            if start_date is not None:
                statement = statement.where(
                    func.date(Expense.transaction_date) >= start_date
                )
            if end_date is not None:
                statement = statement.where(
                    func.date(Expense.transaction_date) <= end_date
                )

        if min_value is not None:
            statement = statement.where(Expense.amount >= max(0, min_value))
        if max_value is not None:
            statement = statement.where(Expense.amount <= max(0, max_value))

        count_statement = select(func.count()).select_from(statement.subquery())

        total_count = (
            (await self.db.execute(count_statement)).scalar() or 0
        )  # Return 0 instead of None if no such expense. Otherwise return the count

        max_limit = 50

        safe_page = max(1, page)  # Sanitize for positive value
        safe_limit = min(limit, max_limit)  # ensure limit is positive and at most 50.

        statement = statement.order_by(
            Expense.transaction_date.desc(), Expense.id.desc()
        )

        statement = statement.offset((safe_page - 1) * safe_limit).limit(
            safe_limit
        )  # Subtracting 1 as default page is 1 which is first page with no offset

        result = await self.db.execute(statement)
        result_list = list(result.scalars().all())

        meta = MetaSchema(
            total=total_count,
            count=len(result_list),
            page=safe_page,
            total_pages=ceil(total_count / safe_limit),
        )
        return PaginatedResponseSchema(data=result_list, meta=meta)
