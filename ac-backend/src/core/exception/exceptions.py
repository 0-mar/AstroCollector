from http import HTTPStatus


class ACException(Exception):
    """Base exception for all errors in the project"""

    def __init__(self, message: str, code: str, http_status: int) -> None:
        super().__init__(message)
        self._message: str = message
        self._code: str = code
        self._http_status: int = http_status

    def __str__(self) -> str:
        return f"{self.__class__.__name__} [status='{self._http_status}', code='{self._code}', message='{self._message}']"


class APIException(ACException):
    CODE = "API_ERROR"
    HTTP_STATUS = HTTPStatus.BAD_REQUEST

    def __init__(self, message: str) -> None:
        super().__init__(message, self.CODE, self.HTTP_STATUS)
