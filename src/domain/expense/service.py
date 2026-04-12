from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID
from math import ceil

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError

from src.common.base_service import BaseService
from src.domain.category.service import CategoryService
from src.domain.expense.schemas import (
    ExpenseCreateSchema,
    ExpenseSchema,
    ExpenseUpdateSchema,
    PaginatedResponseSchema,
    MetaSchema
)
from src.exceptions import DatabaseException, EntityNotFoundException
from src.models import Expense


class ExpenseService(
    BaseService[Expense, ExpenseCreateSchema, ExpenseSchema, ExpenseUpdateSchema]
):
    async def create(self, data: ExpenseCreateSchema, user_id: UUID) -> Expense:

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

        return expense

    async def update(
        self, object_id: Any, data: ExpenseUpdateSchema, user_id: UUID
    ) -> Expense:
        expense = await self.get_by_id(object_id, user_id)

        if data.category_id is not None:
            category_service = CategoryService(self.db)
            await category_service.get_by_id(data.category_id, user_id)

        # Since exclude_none will ignore all fields
        # and sometimes we want get category_id set to None
        # The use of exclude_none here is not suitable
        # So we need to manually loop through the fields and set
        # them if they are not None (except for category_id which can be set to None)

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
            return expense
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

    async def delete(self, object_id: Any, user_id: UUID) -> Expense:
        expense = await self.get_by_id(object_id, user_id)

        try:
            await self.db.delete(expense)
            await self.db.commit()
            return expense
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
        statement = select(Expense).where(
            Expense.id == object_id, Expense.user_id == user_id
        )
        result = await self.db.execute(statement)
        expense = result.scalar_one_or_none()

        if not expense:
            raise EntityNotFoundException(entity_name="Expense", object_id=object_id)

        return expense

    async def get_all(
        self,
        user_id: UUID,
        page:int  = 1,
        limit: int = 20,
        date_filter: date | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        min_value: Decimal | None = None,
        max_value: Decimal | None = None,
    ) -> PaginatedResponseSchema:
        statement = select(Expense).where(Expense.user_id == user_id) #statement for extraction
        
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
        total_count = (await self.db.execute(count_statement)).scalar() or 0 #Return 0 instead of None if no such expense. Otherwise return the count

        max_limit = 50

        safe_page = max(1, page) #Sanitize for positive value
        safe_limit = min(limit, max_limit) #ensure max limit on page size

        statement = statement.offset((safe_page - 1)* limit).limit(safe_limit) #Subtracting 1 as default page is 1 which is first page with no offset      
        
        statement = statement.order_by(
            Expense.transaction_date.desc(), Expense.id.desc()
        )

        result = await self.db.execute(statement)
        result_list =  list(result.scalars().all())

        meta = MetaSchema(total = total_count, count = len(result_list), page = safe_page, total_pages=ceil(total_count/safe_limit))
        return PaginatedResponseSchema(data=result_list, meta = meta)
        
        
        
