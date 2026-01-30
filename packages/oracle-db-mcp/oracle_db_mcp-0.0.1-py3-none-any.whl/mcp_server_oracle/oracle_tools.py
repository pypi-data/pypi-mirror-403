import oracledb
import asyncio
import os

connection_string = ""

# Use Thick mode if ORACLE_THICK_MODE is set to "true"
if os.getenv("ORACLE_THICK_MODE", "false").lower() == "true":
    lib_dir = os.getenv("ORACLE_CLIENT_LIB_DIR", None)
    oracledb.init_oracle_client(lib_dir=lib_dir)

async def list_tables(pattern: str = None, limit: int = 50, offset: int = 0) -> str:
    """Get a list of tables with optional filtering and pagination"""
    try:
        def db_operation(pat, lim, off):
            with oracledb.connect(connection_string) as conn:
                cursor = conn.cursor()
                if pat:
                    cursor.execute(
                        """SELECT table_name FROM user_tables 
                           WHERE table_name LIKE :pattern 
                           ORDER BY table_name 
                           OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY""",
                        pattern=f"%{pat.upper()}%", offset=off, limit=lim
                    )
                else:
                    cursor.execute(
                        """SELECT table_name FROM user_tables 
                           ORDER BY table_name 
                           OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY""",
                        offset=off, limit=lim
                    )
                tables = [row[0] for row in cursor]
                return '\n'.join(tables) if tables else "No tables found"

        return await asyncio.to_thread(db_operation, pattern, limit, offset)
    except oracledb.DatabaseError as e:
        print('Error occurred:', e)
        return str(e)


async def list_schemas() -> str:
    """Get a list of all schemas in the database"""
    try:
        def db_operation():
            with oracledb.connect(connection_string) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT username FROM all_users ORDER BY username")
                schemas = [row[0] for row in cursor]
            return '\n'.join(schemas)

        return await asyncio.to_thread(db_operation)
    except oracledb.DatabaseError as e:
        print('Error occurred:', e)
        return str(e)


async def list_objects(schema_name: str = None, object_type: str = None, limit: int = 100) -> str:
    """List database objects with optional type filter"""
    try:
        def db_operation(schema, obj_type, lim):
            with oracledb.connect(connection_string) as conn:
                cursor = conn.cursor()
                
                if obj_type:
                    type_filter = "AND object_type = :obj_type"
                    type_param = obj_type.upper()
                else:
                    type_filter = "AND object_type IN ('TABLE', 'VIEW', 'SEQUENCE', 'PACKAGE', 'FUNCTION', 'PROCEDURE')"
                    type_param = None
                
                if schema:
                    sql = f"""SELECT object_type, object_name 
                             FROM all_objects 
                             WHERE owner = :schema {type_filter}
                             ORDER BY object_type, object_name
                             FETCH FIRST :limit ROWS ONLY"""
                    if type_param:
                        cursor.execute(sql, schema=schema.upper(), obj_type=type_param, limit=lim)
                    else:
                        cursor.execute(sql, schema=schema.upper(), limit=lim)
                else:
                    sql = f"""SELECT object_type, object_name 
                             FROM user_objects 
                             WHERE 1=1 {type_filter}
                             ORDER BY object_type, object_name
                             FETCH FIRST :limit ROWS ONLY"""
                    if type_param:
                        cursor.execute(sql, obj_type=type_param, limit=lim)
                    else:
                        cursor.execute(sql, limit=lim)
                
                result = ["OBJECT_TYPE,OBJECT_NAME"]
                for row in cursor:
                    result.append(f"{row[0]},{row[1]}")
                
                return '\n'.join(result)

        return await asyncio.to_thread(db_operation, schema_name, object_type, limit)
    except oracledb.DatabaseError as e:
        print('Error occurred:', e)
        return str(e)


async def get_object_details(object_name: str, object_type: str = "TABLE") -> str:
    """Get detailed information about a database object"""
    try:
        def db_operation(obj_name, obj_type):
            with oracledb.connect(connection_string) as conn:
                cursor = conn.cursor()
                result = []
                
                if obj_type.upper() == "TABLE":
                    # Get columns
                    result.append("=== COLUMNS ===")
                    result.append("COLUMN_NAME,DATA_TYPE,NULLABLE,DATA_LENGTH")
                    cursor.execute(
                        """SELECT column_name, data_type, nullable, data_length 
                           FROM user_tab_columns 
                           WHERE table_name = :obj_name 
                           ORDER BY column_id""",
                        obj_name=obj_name.upper()
                    )
                    for row in cursor:
                        result.append(f"{row[0]},{row[1]},{row[2]},{row[3]}")
                    
                    # Get constraints
                    result.append("\n=== CONSTRAINTS ===")
                    result.append("CONSTRAINT_NAME,CONSTRAINT_TYPE,COLUMN_NAME")
                    cursor.execute(
                        """SELECT c.constraint_name, c.constraint_type, cc.column_name
                           FROM user_constraints c
                           JOIN user_cons_columns cc ON c.constraint_name = cc.constraint_name
                           WHERE c.table_name = :obj_name
                           ORDER BY c.constraint_type, c.constraint_name, cc.position""",
                        obj_name=obj_name.upper()
                    )
                    for row in cursor:
                        result.append(f"{row[0]},{row[1]},{row[2]}")
                    
                    # Get indexes
                    result.append("\n=== INDEXES ===")
                    result.append("INDEX_NAME,UNIQUENESS,COLUMN_NAME")
                    cursor.execute(
                        """SELECT i.index_name, i.uniqueness, ic.column_name
                           FROM user_indexes i
                           JOIN user_ind_columns ic ON i.index_name = ic.index_name
                           WHERE i.table_name = :obj_name
                           ORDER BY i.index_name, ic.column_position""",
                        obj_name=obj_name.upper()
                    )
                    for row in cursor:
                        result.append(f"{row[0]},{row[1]},{row[2]}")
                
                elif obj_type.upper() == "VIEW":
                    result.append("=== VIEW DEFINITION ===")
                    cursor.execute(
                        "SELECT text FROM user_views WHERE view_name = :obj_name",
                        obj_name=obj_name.upper()
                    )
                    row = cursor.fetchone()
                    if row:
                        result.append(row[0])
                
                elif obj_type.upper() == "SEQUENCE":
                    result.append("=== SEQUENCE INFO ===")
                    result.append("MIN_VALUE,MAX_VALUE,INCREMENT_BY,LAST_NUMBER")
                    cursor.execute(
                        """SELECT min_value, max_value, increment_by, last_number
                           FROM user_sequences WHERE sequence_name = :obj_name""",
                        obj_name=obj_name.upper()
                    )
                    row = cursor.fetchone()
                    if row:
                        result.append(f"{row[0]},{row[1]},{row[2]},{row[3]}")
                
                return '\n'.join(result) if result else f"Object {obj_name} not found"

        return await asyncio.to_thread(db_operation, object_name, object_type)
    except oracledb.DatabaseError as e:
        print('Error occurred:', e)
        return str(e)


async def get_top_queries(limit: int = 10) -> str:
    """Get the slowest queries based on elapsed time"""
    try:
        def db_operation(query_limit):
            with oracledb.connect(connection_string) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """SELECT sql_id, 
                              ROUND(elapsed_time/1000000, 2) as elapsed_sec,
                              executions,
                              ROUND(elapsed_time/executions/1000000, 2) as avg_elapsed_sec,
                              SUBSTR(sql_text, 1, 100) as sql_text
                       FROM v$sql
                       WHERE executions > 0
                       ORDER BY elapsed_time DESC
                       FETCH FIRST :limit ROWS ONLY""",
                    limit=query_limit
                )
                
                result = ["SQL_ID,ELAPSED_SEC,EXECUTIONS,AVG_ELAPSED_SEC,SQL_TEXT"]
                for row in cursor:
                    sql_text = row[4].replace('\n', ' ').replace(',', ';')
                    result.append(f"{row[0]},{row[1]},{row[2]},{row[3]},{sql_text}")
                
                return '\n'.join(result)

        return await asyncio.to_thread(db_operation, limit)
    except oracledb.DatabaseError as e:
        print('Error occurred:', e)
        return str(e)


async def explain_query(query: str) -> str:
    """Get the execution plan for a SQL query"""
    try:
        def db_operation(sql):
            with oracledb.connect(connection_string) as conn:
                cursor = conn.cursor()
                
                # Generate unique statement ID
                import time
                stmt_id = f"STMT_{int(time.time())}"
                
                # Delete any existing plan
                cursor.execute("DELETE FROM plan_table WHERE statement_id = :stmt_id", stmt_id=stmt_id)
                
                # Explain the query
                explain_sql = f"EXPLAIN PLAN SET STATEMENT_ID = '{stmt_id}' FOR {sql}"
                cursor.execute(explain_sql)
                
                # Retrieve the plan
                cursor.execute(
                    """SELECT LPAD(' ', 2*level-2) || operation || ' ' || options as operation,
                              object_name,
                              cost,
                              cardinality,
                              bytes
                       FROM plan_table
                       WHERE statement_id = :stmt_id
                       START WITH id = 0
                       CONNECT BY PRIOR id = parent_id AND statement_id = :stmt_id
                       ORDER SIBLINGS BY position""",
                    stmt_id=stmt_id
                )
                
                result = ["OPERATION,OBJECT_NAME,COST,CARDINALITY,BYTES"]
                for row in cursor:
                    obj_name = row[1] if row[1] else ""
                    cost = row[2] if row[2] else ""
                    card = row[3] if row[3] else ""
                    bytes_val = row[4] if row[4] else ""
                    result.append(f"{row[0]},{obj_name},{cost},{card},{bytes_val}")
                
                # Cleanup
                cursor.execute("DELETE FROM plan_table WHERE statement_id = :stmt_id", stmt_id=stmt_id)
                conn.commit()
                
                return '\n'.join(result)

        return await asyncio.to_thread(db_operation, query)
    except oracledb.DatabaseError as e:
        print('Error occurred:', e)
        return str(e)


async def analyze_db_health(include_all_invalid: bool = False) -> str:
    """Perform comprehensive database health checks"""
    try:
        def db_operation(show_all):
            with oracledb.connect(connection_string) as conn:
                cursor = conn.cursor()
                result = []
                
                # Tablespace usage
                result.append("=== TABLESPACE USAGE ===")
                result.append("TABLESPACE_NAME,TOTAL_MB,USED_MB,FREE_MB,USED_PCT")
                cursor.execute(
                    """SELECT df.tablespace_name,
                              ROUND(df.total_space/1024/1024, 2) as total_mb,
                              ROUND((df.total_space - fs.free_space)/1024/1024, 2) as used_mb,
                              ROUND(fs.free_space/1024/1024, 2) as free_mb,
                              ROUND(((df.total_space - fs.free_space)/df.total_space)*100, 2) as used_pct
                       FROM (SELECT tablespace_name, SUM(bytes) as total_space
                             FROM dba_data_files GROUP BY tablespace_name) df,
                            (SELECT tablespace_name, SUM(bytes) as free_space
                             FROM dba_free_space GROUP BY tablespace_name) fs
                       WHERE df.tablespace_name = fs.tablespace_name
                       ORDER BY used_pct DESC"""
                )
                for row in cursor:
                    result.append(f"{row[0]},{row[1]},{row[2]},{row[3]},{row[4]}")
                
                # Session count
                result.append("\n=== SESSION STATUS ===")
                result.append("STATUS,COUNT")
                cursor.execute(
                    """SELECT status, COUNT(*) 
                       FROM v$session 
                       GROUP BY status 
                       ORDER BY status"""
                )
                for row in cursor:
                    result.append(f"{row[0]},{row[1]}")
                
                # Top wait events
                result.append("\n=== TOP WAIT EVENTS ===")
                result.append("EVENT,TOTAL_WAITS,TIME_WAITED_SEC")
                cursor.execute(
                    """SELECT event, total_waits, ROUND(time_waited/100, 2) as time_waited_sec
                       FROM v$system_event
                       WHERE wait_class != 'Idle'
                       ORDER BY time_waited DESC
                       FETCH FIRST 10 ROWS ONLY"""
                )
                for row in cursor:
                    result.append(f"{row[0]},{row[1]},{row[2]}")
                
                # Invalid objects
                result.append("\n=== INVALID OBJECTS ===")
                result.append("OWNER,OBJECT_TYPE,OBJECT_NAME")
                
                if show_all:
                    cursor.execute(
                        """SELECT owner, object_type, object_name
                           FROM dba_objects
                           WHERE status = 'INVALID'
                           ORDER BY owner, object_type, object_name"""
                    )
                else:
                    cursor.execute(
                        """SELECT owner, object_type, object_name
                           FROM dba_objects
                           WHERE status = 'INVALID'
                           ORDER BY owner, object_type, object_name
                           FETCH FIRST 20 ROWS ONLY"""
                    )
                
                invalid_count = 0
                for row in cursor:
                    result.append(f"{row[0]},{row[1]},{row[2]}")
                    invalid_count += 1
                
                if not show_all and invalid_count == 20:
                    result.append("... (showing first 20, use include_all_invalid=True for all)")
                
                return '\n'.join(result)

        return await asyncio.to_thread(db_operation, include_all_invalid)
    except oracledb.DatabaseError as e:
        print('Error occurred:', e)
        return str(e)


async def describe_table(table_name: str) -> str:
    try:
        # Run database operations in a separate thread
        def db_operation(table):
            with oracledb.connect(connection_string) as conn:
                cursor = conn.cursor()

                # Create CSV headers
                result = [
                    "COLUMN_NAME,DATA_TYPE,NULLABLE,DATA_LENGTH,PRIMARY_KEY,FOREIGN_KEY"]

                # Get primary key columns
                pk_columns = []
                cursor.execute(
                    """
                    SELECT cols.column_name
                    FROM all_constraints cons, all_cons_columns cols
                    WHERE cons.constraint_type = 'P'
                    AND cons.constraint_name = cols.constraint_name
                    AND cons.owner = cols.owner
                    AND cols.table_name = :table_name
                    """,
                    table_name=table.upper()
                )
                for row in cursor:
                    pk_columns.append(row[0])

                # Get foreign key columns and references
                fk_info = {}
                cursor.execute(
                    """
                    SELECT a.column_name, c_pk.table_name as referenced_table, b.column_name as referenced_column
                    FROM all_cons_columns a
                    JOIN all_constraints c ON a.owner = c.owner AND a.constraint_name = c.constraint_name
                    JOIN all_constraints c_pk ON c.r_owner = c_pk.owner AND c.r_constraint_name = c_pk.constraint_name
                    JOIN all_cons_columns b ON c_pk.owner = b.owner AND c_pk.constraint_name = b.constraint_name
                    WHERE c.constraint_type = 'R'
                    AND a.table_name = :table_name
                    """,
                    table_name=table.upper()
                )
                for row in cursor:
                    fk_info[row[0]] = f"{row[1]}.{row[2]}"

                # Get main column information
                cursor.execute(
                    """
                    SELECT column_name, data_type, nullable, data_length 
                    FROM user_tab_columns 
                    WHERE table_name = :table_name 
                    ORDER BY column_id
                    """,
                    table_name=table.upper()
                )

                rows_found = False
                for row in cursor:
                    rows_found = True
                    column_name = row[0]
                    data_type = row[1]
                    nullable = row[2]
                    data_length = str(row[3])
                    is_pk = "YES" if column_name in pk_columns else "NO"
                    fk_ref = fk_info.get(column_name, "NO")

                    # Format as CSV row
                    result.append(
                        f"{column_name},{data_type},{nullable},{data_length},{is_pk},{fk_ref}")

                if not rows_found:
                    return f"Table {table} not found or has no columns."

                return '\n'.join(result)

        return await asyncio.to_thread(db_operation, table_name)
    except oracledb.DatabaseError as e:
        print('Error occurred:', e)
        return str(e)


async def read_query(query: str, max_rows: int = 100) -> str:
    try:
        # Check if the query is a SELECT statement
        if not query.strip().upper().startswith('SELECT'):
            return "Error: Only SELECT statements are supported."

        # Run database operations in a separate thread
        def db_operation(sql, max_r):
            with oracledb.connect(connection_string) as conn:
                cursor = conn.cursor()
                cursor.execute(sql)

                # Get column names after executing the query
                columns = [col[0] for col in cursor.description]
                result = [','.join(columns)]

                # Process rows with limit
                row_count = 0
                for row in cursor:
                    if row_count >= max_r:
                        result.append(f"... (limited to {max_r} rows)")
                        break
                    string_values = [
                        str(val) if val is not None else "NULL" for val in row]
                    result.append(','.join(string_values))
                    row_count += 1

                return '\n'.join(result)

        return await asyncio.to_thread(db_operation, query, max_rows)
    except oracledb.DatabaseError as e:
        print('Error occurred:', e)
        return str(e)


async def exec_dml_sql(execsql: str) -> str:
    try:
        # Check if SQL statement contains DML keywords
        sql_upper = execsql.upper()
        if not any(keyword in sql_upper for keyword in ['INSERT', 'DELETE', 'TRUNCATE', 'UPDATE']):
            return "Error: Only INSERT, DELETE, TRUNCATE or UPDATE statements are supported."
        
        # Run database operations in a separate thread
        def db_operation(query):
            with oracledb.connect(connection_string) as conn:
                cursor = conn.cursor()
                # Execute DML statement
                cursor.execute(query)
                # Get affected rows count
                rows_affected = cursor.rowcount
                # Commit transaction
                conn.commit()
                # Return execution result
                return f"Execution successful: {rows_affected} rows affected"

        return await asyncio.to_thread(db_operation, execsql)
    except oracledb.DatabaseError as e:
        print('Error occurred:', e)
        return str(e)

async def exec_ddl_sql(execsql: str) -> str:
    try:
        # Check if SQL statement contains DDL keywords
        sql_upper = execsql.upper()
        if not any(keyword in sql_upper for keyword in ['CREATE', 'ALTER', 'DROP']):
            return "Error: Only CREATE, ALTER, DROP statements are supported."
        
        def db_operation(query):
            with oracledb.connect(connection_string) as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                return "DDL statement executed successfully"

        return await asyncio.to_thread(db_operation, execsql)
    except oracledb.DatabaseError as e:
        print('Error occurred:', e)
        return str(e)

async def exec_pro_sql(execsql: str) -> str:
    try:
        # Run database operations in a separate thread
        def db_operation(query):
            with oracledb.connect(connection_string) as conn:
                cursor = conn.cursor()
                # Execute PL/SQL block
                cursor.execute(query)
                # Try to fetch output parameters or return values
                try:
                    result = cursor.fetchall()
                    if result:
                        # Format result as string
                        return '\n'.join(','.join(str(col) if col is not None else 'NULL' for col in row) for row in result)
                except oracledb.DatabaseError:
                    # No result set means it's a stored procedure or PL/SQL block without return value
                    pass
                # Commit transaction
                conn.commit()
                return "PL/SQL block executed successfully"

        return await asyncio.to_thread(db_operation, execsql)
    except oracledb.DatabaseError as e:
        print('Error occurred:', e)
        return str(e)

if __name__ == "__main__":
    # Create and run the async event loop
    async def main():
        # print(await list_tables())
        print(await describe_table('CONCAT'))

    asyncio.run(main())
