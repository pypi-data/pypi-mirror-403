"""query for user"""

qry_dic = dict()


qry_dic.update(
    {
        "read_user_id_all": """
SELECT  user_id
FROM    t_user
"""
    }
)

qry_dic.update(
    {
        "read_user_search": """
SELECT  user_id, user_name, insert_time, update_time
FROM    t_user
WHERE   1 = 1
#if user_id
        AND user_id = %(user_id)s
#elif user_name
        AND user_name ILIKE %(user_name)s
#endif
"""
    }
)

qry_dic.update(
    {
        "read_user_alias": """
SELECT  user_id "Id|아이디", user_name "Name|이름"
FROM    t_user
WHERE   user_id = %(user_id)s
"""
    }
)

qry_dic.update(
    {
        "read_csv_partial": """
SELECT  row_number() OVER (ORDER BY 1) rnum,
        TO_CHAR(generate_series, 'YYYY년 MM월 DD일') each_day
FROM    generate_series(
            '2001-01-01'::timestamp,
            '2025-12-31'::timestamp,
            '1 day'::interval
        )
"""
    }
)
