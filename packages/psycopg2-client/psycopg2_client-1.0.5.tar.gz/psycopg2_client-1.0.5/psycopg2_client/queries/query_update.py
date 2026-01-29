"""query for schema"""

qry_dic = dict()

qry_dic.update(
    {
        "create_tables": """
CREATE TABLE IF NOT EXISTS t_user (
    user_id VARCHAR(50) NOT NULL,
    user_name VARCHAR(100) NOT NULL,
    insert_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    update_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT t_user_pkey PRIMARY KEY (user_id)
)
"""
    }
)

qry_dic.update(
    {
        "upsert_user": """
WITH t AS (
    INSERT INTO t_user
        (
            user_id, user_name
        )
    VALUES
        (
            %(user_id)s, %(user_name)s
        )
    ON CONFLICT (user_id)
    DO UPDATE
    SET     user_name = %(user_name)s,
            update_time = NOW()
    RETURNING user_name
)
SELECT  user_name
FROM    t;
"""
    }
)

qry_dic.update(
    {
        "delete_user": """
DELETE
FROM    t_user
WHERE   user_id = %(user_id)s
"""
    }
)
