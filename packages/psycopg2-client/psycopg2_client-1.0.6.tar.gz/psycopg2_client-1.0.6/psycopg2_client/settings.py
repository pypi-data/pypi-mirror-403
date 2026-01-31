"""settings"""

from dataclasses import dataclass
from typing import Callable

# pylint: disable=relative-beyond-top-level
from .query_by_key.settings import Settings as QrySettings


@dataclass(frozen=True)
class Settings(QrySettings):
    """db client settings"""

    host: str
    port: int
    database: str
    user: str
    password: str

    minconn: int
    maxconn: int
    connect_timeout: int

    before_read_execute: Callable[[str, dict, str, str], None]
    """
    qry_key: str, params: dict, qry_str: str, qry_with_value: str
    """
    after_read_execute: Callable[[str, int], None]
    """
    qry_key: str, duration: int
    """
    before_update_execute: Callable[
        [str, dict, dict, str, str],
        None,
    ]
    """
    qry_key: str, params: dict, params_out: dict, qry_str: str, qry_with_value: str
    """
    after_update_execute: Callable[[str, int, dict, int], None]
    """
    qry_key: str, row_count: int, params_out: dict, duration: int
    """

    @property
    def key(self):
        """key for another dictionary"""

        return (
            f"{self.host},{self.port},{self.database},{self.user},{self.password}"
            f"{self.minconn},{self.maxconn},{self.connect_timeout}"
        )
