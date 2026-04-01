class AppException(Exception):
    status_code: int = 500
    error_code: str = "internal_error"
    message: str = "Internal Error Occurred"

    def __init__(self, message: str | None = None, context: dict | None = None):
        self.message = message or self.message
        self.context = context or {}

        super().__init__(self.message)


class EntityNotFoundException(AppException):
    status_code: int = 404
    error_code: str = "entity_not_found"
    message: str = "Requested entity was not found"

    def __init__(self, entity_name: str, object_id: str | int):
        super().__init__(
            message=f"{entity_name} with id '{object_id}' was not found",
            context={"entity_name": entity_name, "object_id": object_id},
        )


class DatabaseException(AppException):
    status_code: int = 500
    error_code: str = "database_error"
    message: str = "Database operation failed"

    def __init__(self, operation: str, entity_name: str, details: dict | None = None):
        context = {"operation": operation, "entity_name": entity_name}
        if details:
            context["details"] = details
        super().__init__(
            message=f"Database operation failed while {operation} {entity_name}",
            context=context,
        )
