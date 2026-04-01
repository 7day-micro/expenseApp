from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

Model = TypeVar("Model")  # Model
ResponseSchema = TypeVar("Response")  # Schema
CreateSchema = TypeVar("Create")  # Schema


class BaseService(ABC, Generic[Model, CreateSchema, ResponseSchema]):
    """
    Base service class that defines the common CRUD operations for all services.

    This class is meant to be inherited by all domain related services:
    - Expense Service
    - Budget Service
    - Category Service

    Each service need to implement this contract to ensure consistency across the application.

    This class uses generics to allow for flexibility in the types of models and schemas that can be used.

    Attributes:
        db (AsyncSession): The database session used for performing database operations.

    """

    def __init__(self, db: "AsyncSession"):
        self.db = db

    @abstractmethod
    async def create(self, data: CreateSchema, user_id: UUID) -> Model:
        """
        data : The data to create a new record, typically a Pydantic schema. these schemas are defined in /src/domain/[domain_name]/schemas.py
        user_id : The ID of the user performing the operation, used for associating the record


        Raises:
            TODO : define custom exception

        """
        pass

    @abstractmethod
    async def update(
        self, object_id: Any, data: CreateSchema, user_id: UUID
    ) -> Optional[Model]:
        """
        Update an existing record identified by `object_id` with `data` for the given `user_id`.
        
        Parameters:
            object_id: Identifier of the record to update.
            data: Payload containing fields to update.
            user_id: Identifier of the user performing the operation.
        
        Returns:
            The updated `Model` instance.
        
        Raises:
            EntityNotFoundException: if the record does not exist.
        """
        pass

    @abstractmethod
    async def delete(self, object_id: Any, user_id: UUID) -> Optional[Model]:
        """
        Delete the record identified by `object_id` that is associated with `user_id`.
        
        Parameters:
            object_id (Any): Identifier of the record to delete.
            user_id (UUID): Identifier of the user who owns the record; implementers must restrict deletion to this user's records.
        
        Returns:
            Optional[Model]: The deleted model instance if deletion occurred, `None` if no deletion was performed.
        
        Raises:
            EntityNotFoundException: If the record does not exist.
        """
        pass

    @abstractmethod
    async def get_by_id(self, object_id: Any, user_id: UUID) -> Optional[Model]:
        """
        Retrieve a single record by its identifier, restricted to the provided user.
        
        Parameters:
            object_id: Identifier of the record to retrieve.
            user_id: UUID of the user whose scope should be used to filter the record.
        
        Returns:
            The matching model instance.
        
        Raises:
            EntityNotFoundException: if the record does not exist.
        """
        pass

    @abstractmethod
    async def get_all(self, user_id: UUID) -> List[Model]:
        """
        user_id : The ID of the user performing the operation, used for associating the records

        user_id for this type of operation is crucial as it ensures that users can only access their own records,
        maintaining data privacy and security across the application.

        Who implement this method should ensure that the query filters records based on
        the user_id to return only the relevant data for the user.

        """
        pass
