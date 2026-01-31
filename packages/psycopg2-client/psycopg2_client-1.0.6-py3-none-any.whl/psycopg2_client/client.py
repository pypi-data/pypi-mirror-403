"""database client"""

import csv
from datetime import datetime
import time
import io
import atexit
from typing import AsyncGenerator, Generator
from psycopg2 import pool
from psycopg2.extras import RealDictCursor, RealDictRow
from psycopg2.extensions import connection

# pylint: disable=relative-beyond-top-level
from .query_by_key.query_util import (
    get_query_with_value,
)
from .query_by_key.query import Query
from .query_by_key.settings import Settings as QrySettings
from .settings import Settings


class ClientPool:
    """database connection pool"""

    def __init__(self, db_settings_pool: Settings):
        self.conn_pool = pool.ThreadedConnectionPool(
            minconn=db_settings_pool.minconn,
            maxconn=db_settings_pool.maxconn,
            connect_timeout=db_settings_pool.connect_timeout,
            host=db_settings_pool.host,
            port=db_settings_pool.port,
            database=db_settings_pool.database,
            user=db_settings_pool.user,
            password=db_settings_pool.password,
        )

        print(datetime.now(), self.__class__.__name__, self.__init__.__name__)

    def __exit__(self, exc_type, exc_value, traceback):
        """Close the shared connection pool."""
        if self.conn_pool:
            self.conn_pool.closeall()

            print(datetime.now(), self.__class__.__name__, self.__exit__.__name__)

    def getconn(self) -> connection:
        """return conn_pool"""
        return self.conn_pool.getconn()

    def putconn(self, conn):
        """putconn"""
        self.conn_pool.putconn(conn)


db_set_and_pool: dict[str, ClientPool] = {}


class Client:
    """database client"""

    # Class-level shared connection pool
    _conn_pool: ClientPool

    def __init__(self, db_settings: Settings):
        # pylint:disable=global-statement,global-variable-not-assigned
        global db_set_and_pool

        self.conn: connection
        self.in_with_block = False
        self.db_settings = db_settings
        self.qry = Query(
            qry_settings=QrySettings(
                use_en_ko_column_alias=db_settings.use_en_ko_column_alias,
                use_conditional=db_settings.use_conditional,
                all_query=db_settings.all_query,
            )
        )
        self.query_recent = ""

        db_set_key = db_settings.key
        if db_set_key not in db_set_and_pool:
            client_pool = ClientPool(db_settings)
            db_set_and_pool[db_set_key] = client_pool
            Client._conn_pool = client_pool

    def __enter__(self):
        # Called when entering the 'with' block
        self.conn = Client._conn_pool.getconn()
        self.in_with_block = True
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # Called when exiting the 'with' block
        try:
            if exc_type is None:
                # No exception, commit the transaction
                self.conn.commit()
            else:
                # Exception occurred, rollback the transaction
                self.conn.rollback()
        finally:
            if self.conn:
                self._conn_pool.putconn(self.conn)

            self.in_with_block = False

    def read_rows(
        self,
        qry_key: str,
        params: dict,
        *,
        en: bool = False,
        fetchone: bool = False,
    ) -> list[RealDictRow]:
        """Returns all rows

        Arguments:
            qry_key: Key of the Dictionary registered in the clients/queries folder
            params: Key, Value pairs to pass as parameters to the SQL query.

        Returns:
            a List of Dictionaries;
        """

        def read_rows_by_param(
            qry_key: str,
            params: dict,
            *,
            en: bool = False,
            fetchone: bool = False,
            cursor: RealDictCursor,
        ):
            if not isinstance(params, dict):
                params = vars(params)

            qry_str = self.qry.get_query_by_key(qry_key, params, "read", en)

            start = 0
            if self.db_settings.before_read_execute:
                self.db_settings.before_read_execute(
                    qry_key,
                    params,
                    qry_str,
                    get_query_with_value(qry_str, params),
                )
                start = time.time()

            rows: list[RealDictRow] = []
            cursor.execute(qry_str, params)

            if not fetchone:
                rows = cursor.fetchall()
            else:
                row = cursor.fetchone()
                if row:
                    rows.append(row)

            if self.db_settings.after_read_execute:
                duration = int(round((time.time() - start) * 1000))
                self.db_settings.after_read_execute(qry_key, duration)

            if not rows:
                return rows

            return rows

        rows: list[RealDictRow] = []
        if self.in_with_block:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            rows = read_rows_by_param(
                qry_key,
                params,
                en=en,
                fetchone=fetchone,
                cursor=cursor,
            )
        else:
            conn_pool = Client._conn_pool
            conn = conn_pool.getconn()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            try:
                rows = read_rows_by_param(
                    qry_key,
                    params,
                    en=en,
                    fetchone=fetchone,
                    cursor=cursor,
                )
            finally:
                cursor.close()
                conn_pool.putconn(conn)

        return rows

    def read_row(
        self,
        qry_key: str,
        params: dict,
        *,
        en: bool = False,
    ) -> RealDictRow | None:
        """call read_rows"""

        rows = self.read_rows(
            qry_key,
            params,
            en=en,
            fetchone=True,
        )
        if not rows:
            return None

        return rows[0]

    async def read_csv_partial_async(
        self,
        qry_key: str,
        params: dict,
        *,
        row_count_partial: int = 100,
        en: bool = False,
    ) -> AsyncGenerator[bytes, None]:
        """Return rows partially in batches with async

        Arguments:
            qry_key: key of the Dictionary registered in the clients/queries folder
            params: key, value pairs to pass as parameters to the SQL query.
            row_count_partial: Number of rows to return at a time

        Returns:
            CSV format converted to UTF-8-BOM
        """

        async def read_csv_partial_async_by_param(
            qry_key: str,
            params: dict,
            *,
            row_count_partial: int = 100,
            en: bool = False,
            cursor: RealDictCursor,
        ) -> AsyncGenerator[bytes, None]:
            if not isinstance(params, dict):
                params = vars(params)

            cursor_name = "cur_partial"
            qry_str = (
                f"DECLARE {cursor_name} CURSOR FOR"
                f" {self.qry.get_query_by_key(qry_key, params, 'csv', en)}"
            )

            rows: list[RealDictRow] = []
            is_second = False

            # without  UTF-8 BOM, hangul will be broken.
            utf8_bom = b"\xef\xbb\xbf"
            yield utf8_bom

            cursor.execute(qry_str, params)
            while True:
                start = 0
                if not is_second:
                    if self.db_settings.before_read_execute:
                        self.db_settings.before_read_execute(
                            qry_key,
                            params,
                            qry_str,
                            get_query_with_value(qry_str, params),
                        )
                        start = time.time()

                cursor.execute(f"FETCH {row_count_partial} FROM {cursor_name}", params)
                rows = cursor.fetchall()

                if not is_second:
                    if self.db_settings.after_read_execute:
                        duration = int(round((time.time() - start) * 1000))
                        self.db_settings.after_read_execute(qry_key, duration)

                if not rows:
                    break

                csv_out = io.StringIO()
                csv_w = csv.writer(csv_out)
                if not is_second and cursor.description:
                    column_names = [desc[0] for desc in cursor.description]
                    csv_w.writerow(column_names)
                csv_w.writerows(rows)

                yield csv_out.getvalue().encode("utf-8")

                is_second = True

        if self.in_with_block:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            async for value in read_csv_partial_async_by_param(
                qry_key,
                params,
                row_count_partial=row_count_partial,
                en=en,
                cursor=cursor,
            ):
                yield value
        else:
            conn_pool = Client._conn_pool
            conn = conn_pool.getconn()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            try:
                async for value in read_csv_partial_async_by_param(
                    qry_key,
                    params,
                    row_count_partial=row_count_partial,
                    en=en,
                    cursor=cursor,
                ):
                    yield value
            finally:
                cursor.close()
                conn_pool.putconn(conn)

    def read_csv_partial(
        self,
        qry_key: str,
        params: dict,
        *,
        row_count_partial: int = 100,
        en: bool = False,
    ) -> Generator[bytes, None, None]:
        """Return rows partially in batches

        Arguments:
            qry_key: key of the Dictionary registered in the clients/queries folder
            params: key, value pairs to pass as parameters to the SQL query.
            row_count_partial: Number of rows to return at a time

        Returns:
            CSV format converted to UTF-8-BOM
        """

        def read_csv_partial_by_param(
            qry_key: str,
            params: dict,
            *,
            row_count_partial: int = 100,
            en: bool = False,
            cursor: RealDictCursor,
        ) -> Generator[bytes, None, None]:
            if not isinstance(params, dict):
                params = vars(params)

            cursor_name = "cur_partial"
            qry_str = (
                f"DECLARE {cursor_name} CURSOR FOR"
                f" {self.qry.get_query_by_key(qry_key, params, 'csv', en)}"
            )

            rows: list[RealDictRow] = []
            is_second = False

            # without UTF-8 BOM, hangul will be broken.
            utf8_bom = b"\xef\xbb\xbf"
            yield utf8_bom

            cursor.execute(qry_str, params)
            while True:
                start = 0
                if not is_second:
                    if self.db_settings.before_read_execute:
                        self.db_settings.before_read_execute(
                            qry_key,
                            params,
                            qry_str,
                            get_query_with_value(qry_str, params),
                        )
                        start = time.time()

                cursor.execute(f"FETCH {row_count_partial} FROM {cursor_name}", params)
                rows = cursor.fetchall()

                if not is_second:
                    if self.db_settings.after_read_execute:
                        duration = int(round((time.time() - start) * 1000))
                        self.db_settings.after_read_execute(qry_key, duration)
                if not rows:
                    break

                csv_out = io.StringIO()
                csv_w = csv.writer(csv_out)
                if not is_second and cursor.description:
                    column_names = [desc[0] for desc in cursor.description]
                    csv_w.writerow(column_names)
                csv_w.writerows(rows)

                yield csv_out.getvalue().encode("utf-8")

                is_second = True

        if self.in_with_block:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            yield from read_csv_partial_by_param(
                qry_key,
                params,
                row_count_partial=row_count_partial,
                en=en,
                cursor=cursor,
            )
        else:
            conn_pool = Client._conn_pool
            conn = conn_pool.getconn()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            try:
                yield from read_csv_partial_by_param(
                    qry_key,
                    params,
                    row_count_partial=row_count_partial,
                    en=en,
                    cursor=cursor,
                )
            finally:
                cursor.close()
                conn_pool.putconn(conn)

    def updates(
        self,
        qry_key_params_list: list[tuple[str, dict, dict]] | list[tuple[str, dict]],
    ) -> list[int]:
        """Executes a list of SQL statements within a single transaction.
        If all SQL commands succeed, returns a list of the number of rows affected by each qry_key.
        If any command fails, an error is raised.

        Arguments:
            qry_key_params_list: A list of tuples, each containing the following two values:
                qry_key: key of the dictionary registered in the clients/queries folder
                params: key, value pairs to pass as parameters to the SQL query.

        Returns:
            A list of the number of rows affected
        """

        def normalize_qry_key_params_list(
            qry_key_params_list: list[any],  # type: ignore
        ) -> list[tuple[str, dict, dict]]:
            """normalize all item from parameter of Psycopg2Client.updates"""

            qry_key_params_list_new: list[tuple[str, dict, dict]] = []
            for item in qry_key_params_list:
                # append params_out if not exists
                item_new: tuple[str, dict, dict] = (
                    item if len(item) == 3 else (item[0], item[1], {})
                )

                qry_key, params, params_out = item_new
                if not isinstance(params, dict):
                    params: dict = vars(params)

                if params_out is None:
                    params_out = {}
                if not isinstance(params_out, dict):
                    params_out: dict = vars(params_out)

                qry_key_params_list_new.append((qry_key, params, params_out))

            return qry_key_params_list_new

        def updates_by_param(
            qry_key_params_list: list[tuple[str, dict, dict]] | list[tuple[str, dict]],
            cursor: RealDictCursor,
        ) -> list[int]:
            row_counts: list[int] = []
            qry_strs: list[str] = []

            qry_key_params_list_new = normalize_qry_key_params_list(qry_key_params_list)

            for item in qry_key_params_list_new:
                qry_key, params, params_out = item

                qry_str = self.qry.get_query_by_key(qry_key, params, "update")

                start = 0
                if self.db_settings.before_update_execute:
                    self.db_settings.before_update_execute(
                        qry_key,
                        params,
                        params_out,
                        qry_str,
                        get_query_with_value(qry_str, params),
                    )
                    start = time.time()

                cursor.execute(qry_str, params)
                row_count = cursor.rowcount

                if params_out:
                    row = cursor.fetchone()
                    if row:
                        for k, v in row.items():
                            if k in params_out:
                                params_out[k] = v

                if self.db_settings.after_update_execute:
                    duration = int(round((time.time() - start) * 1000))
                    self.db_settings.after_update_execute(
                        qry_key, row_count, params_out, duration
                    )

                row_counts.append(row_count)
                qry_strs.append(qry_str)

            return row_counts

        row_counts: list[int] = []
        if self.in_with_block:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            row_counts = updates_by_param(qry_key_params_list, cursor)
        else:
            conn_pool = Client._conn_pool
            try:
                with conn_pool.getconn() as conn:
                    cursor = conn.cursor(cursor_factory=RealDictCursor)
                    row_counts = updates_by_param(qry_key_params_list, cursor)
                    cursor.close()
            finally:
                conn_pool.putconn(conn)  # type: ignore

        return row_counts

    def update(
        self,
        qry_key: str,
        params: dict,
        # pylint: disable=dangerous-default-value
        params_out: dict = {},
    ) -> int:
        """call updates"""

        row_counts = self.updates([(qry_key, params, params_out)])
        return row_counts[0] if row_counts else 0


@atexit.register
def close_all_connection():
    """call when python exits"""

    # pylint:disable=global-statement
    global db_set_and_pool

    for v in db_set_and_pool.values():
        if v:
            v = None
    db_set_and_pool = {}
