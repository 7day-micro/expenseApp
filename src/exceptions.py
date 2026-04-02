from fastapi import HTTPException


class AppException(HTTPException):
    status_code: int = 500
    error_code: str = "internal_error"
    message: str = "Internal Error Occurred"

    def __init__(self, message: str | None = None, context: dict | None = None):
        """
        Initialize the exception with an optional message and context.

        Parameters:
            message (str | None): If provided, overrides the class default message.
            context (dict | None): Additional structured context stored on the exception; defaults to an empty dict.
        """
        self.message = message or self.message
        self.context = context or {}

        super().__init__(status_code=self.status_code, detail=self.message)


class EntityNotFoundException(AppException):
    status_code: int = 404
    error_code: str = "entity_not_found"
    message: str = "Requested entity was not found"

    def __init__(self, entity_name: str, object_id: str | int):
        """
        Initialize an EntityNotFoundException for a missing entity.

        Parameters:
            entity_name (str): The name of the entity type that was not found.
            object_id (str | int): The identifier of the missing entity; may be a string or integer.

        Description:
            Constructs an error message of the form "<entity_name> with id '<object_id>' was not found"
            and provides a context dictionary containing `entity_name` and `object_id` to the base exception.
        """
        super().__init__(
            message=f"{entity_name} with id '{object_id}' was not found",
            context={"entity_name": entity_name, "object_id": object_id},
        )


class DatabaseException(AppException):
    status_code: int = 500
    error_code: str = "database_error"
    message: str = "Database operation failed"

    def __init__(self, operation: str, entity_name: str, details: dict | None = None):
        """
        Initialize the DatabaseException with the failing operation, target entity, and optional details.

        The instance message is set to "Database operation failed while {operation} {entity_name}" and the exception context contains the keys "operation" and "entity_name"; if `details` is provided it is added under the "details" key.

        Parameters:
            operation (str): The database operation that failed (e.g., "insert", "update").
            entity_name (str): The name of the entity (table/model) involved in the operation.
            details (dict | None): Optional additional information about the failure to include in the exception context.
        """
        context = {"operation": operation, "entity_name": entity_name}
        if details:
            context["details"] = details
        super().__init__(
            message=f"Database operation failed while {operation} {entity_name}",
            context=context,
        )
