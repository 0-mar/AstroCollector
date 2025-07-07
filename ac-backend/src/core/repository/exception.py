from http import HTTPStatus

from src.core.exception.exceptions import ACException


class RepositoryException(ACException):
    """Base exception for repository errors."""

    CODE = "DB_SESSION_MANAGER_ERROR"
    HTTP_STATUS = HTTPStatus.INTERNAL_SERVER_ERROR

    def __init__(self, message: str):
        super().__init__(message, self.CODE, self.HTTP_STATUS)
