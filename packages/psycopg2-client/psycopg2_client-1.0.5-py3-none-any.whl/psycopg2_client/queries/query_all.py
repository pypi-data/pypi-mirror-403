"""query collection"""

from .query_update import qry_dic as query_update
from .query_read import qry_dic as query_read

qry_all = [query_update, query_read]

qry_dic = {}
for qry_cur in qry_all:
    dup = qry_dic.keys() & qry_cur.keys()
    if dup:
        raise ValueError(
            f"duplicated keys: {dup} in {qry_dic.keys()} and {qry_cur.keys()}"
        )

    qry_dic |= qry_cur
