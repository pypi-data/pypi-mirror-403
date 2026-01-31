import csv
from io import StringIO
from psycopg2 import sql as pcsql

from sqlalchemy.dialects import postgresql as pgcmd
import sqlalchemy as sa

def records_to_sql(records: iter, con: sa.engine, table: str, schema: str, upsert: bool=False, index_elements: list=None, chunksize=5000, upsert_missing_columns=True) -> bool:
    """ Inserts records into a table. Allows for upserts. This only works on postgresql for now.
    
    Params:
        records (iterator): a list of records in the form of [{col1=val1, col2=val2, col3=val3}]
        con (sqlalchemy engine): a sqlalchemy engine connection
        table (str): destination table name
        schema (str): destination schema name
        upsert (bool): whether to upsert the data. uses postgres dialect ON CONFLICT DO UPDATE
        index_elements (list): a list of column names to match the on conflict statement
        chunksize (int): chunk size to insert on
        upsert_missing_columns (bool): Default True, If True, a missing column will be set to null on upsert.

    Returns:
        True if import was successful
    
    """
    metadata = sa.MetaData()
    table_info = sa.Table(table, metadata, autoload_with=con, schema=schema)
    records = iter(records) # in case the iter is a list.

    if (index_elements is None or len(index_elements) == 0) and upsert:
        raise ValueError('No index_elements defined for the on conflict statement. You must define what columns the on conflict will hit.')

    with con.begin() as conn:
        has_more_data = True
        total_rows = 0
        while has_more_data:
            active_columns = set()
            records_to_insert = []

            for i in range(chunksize):
                try:
                    _ = next(records)
                    active_columns.update(_.keys())
                    records_to_insert.append(_)
                    total_rows += 1

                except StopIteration:
                    has_more_data = False
                    break

            if len(records_to_insert) > 0:
                insert_query = pgcmd.insert(table_info).values(records_to_insert)
                
                # Garbage collector is sometimes slow at removing this.
                del(records_to_insert)
                
                if upsert:
                        if not upsert_missing_columns:
                            try:
                                cols = {col: insert_query.excluded[col] for col in active_columns}
                            except KeyError as e:
                                 raise sa.exc.SQLAlchemyError(f'We are trying to update the column {e}, but it does not exist in {schema}.{table}')
                        else:
                             cols = {**insert_query.excluded}

                        insert_query = insert_query.on_conflict_do_update(
                        index_elements=index_elements,
                        set_=cols
                        )
                try:
                    conn.execute(insert_query)
                    print(f'Inserted {total_rows} rows' + (' so far..' if has_more_data else '.'))
                except sa.exc.SQLAlchemyError as e:
                    # Reraising the error will prevent potential errors that will take up MB of data from
                    #  a failed insert.
                    str_e = str(e)[:2000] + ' <<output truncated>>'
                    raise sa.exc.SQLAlchemyError('got sqlalchemy exception: ' + str_e) from None

    return True

def df_to_sql(df: object, *args, **kwargs):
    """ Wrapper function for records_to_sql(), however accepting a dataframe instead of a records iterator

        Params:
            df (pandas.DataFrame): a DataFrame object
            con (sqlalchemy engine): a sqlalchemy engine connection
            table (str): destination table name
            schema (str): destination schema name
            upsert (bool): upserts the data. uses postgres dialect ON CONFLICT DO UPDATE
            index_elements (list): a list of column names to match the on conflict statement
            chunksize (int): chunk size to insert on

        Returns:
            True if import was successful
    """
    try:
        import pandas as pd
        records = (row.to_dict() for index, row in df.iterrows())
        return records_to_sql(records=records, *args, **kwargs)
    except ImportError:
            raise ImportError('Pandas is not installed or could not be imported.')
    
_NULL_SENTINEL = 'NULLNULLaNULL'

def records_to_sql_fast(records: list, table: str, schema: str, pre_insert_sql: str=None, db_url: str=None, con=None):
    """
    Bulk load records into a PostgreSQL table using COPY.
    
    Args:
        records: List of dictionaries to insert
        db_url: SQLAlchemy database URL (postgresql+psycopg2://...)
        con: sqlalchemy database connection. Must have either db_url or con defined.
        table: Target table name
        schema: Target schema name
        pre_insert_sql: Optional SQL statement to execute before inserting records
    """
    if not records:
        print("No records to insert, skipping")
        return
    
    if con:
        engine = con
    elif db_url:
        engine = sa.create_engine(db_url)
    else:
        raise ValueError('Must have either con or db_url defined.')
    
    with engine.begin() as conn:
        if pre_insert_sql:
            print(f"Executing pre-insert SQL: {pre_insert_sql}")
            conn.execute(sa.text(pre_insert_sql))
        
        tbl_col_names = _get_table_cols(conn=conn, schema=schema, table_name=table)
        rec_count = _copy_from_csv(
            rows=records,
            schema=schema,
            table_name=table,
            conn=conn,
            columns=tbl_col_names
        )
    
    print(f"Successfully loaded {rec_count} records into {schema}.{table}")

def _get_table_cols(conn, schema, table_name):
    """Get column names for a table."""
    meta = sa.MetaData(schema=schema)
    table = sa.Table(table_name, meta, autoload=True, autoload_with=conn)
    return [c.name for c in table.c]


def _dicts_to_csv(rows, columns):
    """Convert list of dictionaries to CSV format for COPY."""
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=columns, quoting=csv.QUOTE_MINIMAL)
    writer.writeheader()
    
    rec_count = 0
    for record in rows:
        row_to_write = {
            col: (_NULL_SENTINEL if record.get(col) is None else record.get(col, _NULL_SENTINEL))
            for col in columns
        }
        writer.writerow(row_to_write)
        rec_count = rec_count + 1
    
    output.seek(0)
    return output, rec_count


def _copy_from_csv(rows, schema, table_name, conn, columns) -> int:
    """Execute PostgreSQL COPY command from CSV data. Returns the number of records inserted."""
    raw_conn = conn.connection
    cursor = raw_conn.cursor()
    
    try:
        csv_data, rec_count = _dicts_to_csv(rows, columns)
        
        copy_sql = pcsql.SQL(
            'COPY {}.{} FROM STDIN WITH (FORMAT csv, NULL {}, HEADER)'
        ).format(
            pcsql.Identifier(schema),
            pcsql.Identifier(table_name),
            pcsql.Literal(_NULL_SENTINEL)
        )
        
        cursor.copy_expert(copy_sql.as_string(cursor), file=csv_data)
        return rec_count
    finally:
        cursor.close()
