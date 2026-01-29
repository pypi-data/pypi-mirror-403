"""settings"""

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class Settings:
    """db client settings"""

    password: str
    host: str
    port: int
    database: str
    user: str

    minconn: int
    maxconn: int
    connect_timeout: int

    use_en_ko_column_alias: bool
    """SELECT file_name "File Name|파일명" """

    use_conditional: bool
    """
    #if target == 'korea'
        FROM tbl_korea
    #else
        FROM tbl_vietnam
    #endif
    """

    before_read_execute: Callable[[str, dict, str, str], None]
    """
    qry_type: str, params: dict, qry_str: str, qry_with_value: str
    """
    after_read_execute: Callable[[str, int], None]
    """
    qry_type: str, duration: int
    """
    before_update_execute: Callable[
        [str, dict, dict, str, str],
        None,
    ]
    """
    qry_type: str, params: dict, params_out: dict, qry_str: str, qry_with_value: str
    """
    after_update_execute: Callable[[str, int, dict, int], None]
    """
    qry_type: str, row_count: int, params_out: dict, duration: int
    """
