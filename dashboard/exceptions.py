
class DashboardException(Exception):
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


class DatabaseException(DashboardException):
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