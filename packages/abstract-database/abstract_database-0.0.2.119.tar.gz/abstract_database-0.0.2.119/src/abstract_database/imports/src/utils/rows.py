from .imports import *
def get_rows(rows):
    if not rows:
        return None
    if isinstance(rows,psycopg2.extras.RealDictRow):
        rows = dict(rows)
    if isinstance(rows, list):
        for i,row in  enumerate(rows):
            if isinstance(row,psycopg2.extras.RealDictRow):
                row = dict(row)
            rows[i] = row
    # If select_rows returned a dict, use it; if it returned a list, grab the first item
    if isinstance(rows, dict):
        return rows
    else:
        return rows
def get_last_row(table_name,**kwargs):
    dbName = kwargs.get('dbName','solcatcher')
    with get_engine(dbName).connect() as conn:
        result = conn.execute(text(f"SELECT * FROM {table_name} ORDER BY id DESC LIMIT 1;"))
        last_row = result.fetchone()
        return last_row
