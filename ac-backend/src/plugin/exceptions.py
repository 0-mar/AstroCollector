from http import HTTPStatus

from src.core.exception.exceptions import ACException


class NoPluginClassException(ACException):
    """Exception for missing plugin class inside module"""

    CODE = "NO_PLUGIN_CLASS_ERROR"
    HTTP_STATUS = HTTPStatus.INTERNAL_SERVER_ERROR

    def __init__(self) -> None:
        super().__init__("No plugin class found in module", self.CODE, self.HTTP_STATUS)
