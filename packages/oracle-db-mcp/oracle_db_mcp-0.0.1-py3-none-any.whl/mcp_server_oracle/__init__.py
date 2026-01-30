import os
import sys
import signal
import argparse
from typing import Any
from mcp.server.fastmcp import FastMCP
from . import oracle_tools
from dotenv import load_dotenv


# Load the environment variables
load_dotenv()

# Initialize the FastMCP server
mcp = FastMCP("mcp-server-oracle")

oracle_tools.connection_string = os.getenv("ORACLE_CONNECTION_STRING")


@mcp.tool()
async def list_tables(pattern: str = None, limit: int = 50, offset: int = 0) -> str:
    """Get a list of all tables in the oracle database with optional filtering and pagination

    Args:
        pattern (string, optional): Filter tables by name pattern (case-insensitive)
        limit (int, optional): Maximum number of tables to return. Default is 50
        offset (int, optional): Number of tables to skip. Default is 0
    """
    return await oracle_tools.list_tables(pattern, limit, offset)


@mcp.tool()
async def list_schemas() -> str:
    """Get a list of all schemas in the oracle database

    Args:
        None
    """
    return await oracle_tools.list_schemas()


@mcp.tool()
async def list_objects(schema_name: str = None, object_type: str = None, limit: int = 100) -> str:
    """List database objects (tables, views, sequences, packages) in a schema

    Args:
        schema_name (string, optional): The schema name to list objects from. If not provided, lists objects from current user's schema
        object_type (string, optional): Filter by object type (TABLE, VIEW, SEQUENCE, PACKAGE, FUNCTION, PROCEDURE)
        limit (int, optional): Maximum number of objects to return. Default is 100
    """
    return await oracle_tools.list_objects(schema_name, object_type, limit)


@mcp.tool()
async def get_object_details(object_name: str, object_type: str = "TABLE") -> str:
    """Get detailed information about a database object

    Args:
        object_name (string): The name of the object
        object_type (string, optional): The type of object (TABLE, VIEW, SEQUENCE). Default is TABLE
    """
    return await oracle_tools.get_object_details(object_name, object_type)


@mcp.tool()
async def get_top_queries(limit: int = 10) -> str:
    """Get the slowest queries based on elapsed time

    Args:
        limit (int, optional): Number of queries to return. Default is 10
    """
    return await oracle_tools.get_top_queries(limit)


@mcp.tool()
async def explain_query(query: str) -> str:
    """Get the execution plan for a SQL query

    Args:
        query (string): The SQL query to explain
    """
    return await oracle_tools.explain_query(query)


@mcp.tool()
async def analyze_db_health(include_all_invalid: bool = False) -> str:
    """Perform comprehensive database health checks including tablespace usage, session status, wait events, and invalid objects

    Args:
        include_all_invalid (bool, optional): If True, return all invalid objects. If False, limit to first 20. Default is False
    """
    return await oracle_tools.analyze_db_health(include_all_invalid)


@mcp.tool()
async def describe_table(table_name: str) -> str:
    """Get a description of a table in the oracle database"

    Args:
        table_name (string): The name of the table to describe
    """
    return await oracle_tools.describe_table(table_name)


@mcp.tool()
async def read_query(query: str, max_rows: int = 100) -> str:
    """Execute SELECT queries to read data from the oracle database

    Args:
        query (string): The SELECT query to execute
        max_rows (int, optional): Maximum number of rows to return. Default is 100
    """
    return await oracle_tools.read_query(query, max_rows)

@mcp.tool()
async def exec_dml_sql(execsql: str) -> str:
    """Execute insert/update/delete/truncate to the oracle database

    Args:
        query (string): The sql to execute
    """
    return await oracle_tools.exec_dml_sql(execsql)

@mcp.tool()
async def exec_ddl_sql(execsql: str) -> str:
    """Execute create/drop/alter to the oracle database

    Args:
        query (string): The sql to execute
    """
    return await oracle_tools.exec_ddl_sql(execsql)

@mcp.tool()
async def exec_pro_sql(execsql: str) -> str:
    """Execute PL/SQL code blocks including stored procedures, functions and anonymous blocks

    Args:
        execsql (string): The PL/SQL code block to execute
    """
    return await oracle_tools.exec_pro_sql(execsql)


def main() -> None:
    parser = argparse.ArgumentParser(description="Oracle Database MCP Server")
    parser.add_argument("--transport", choices=["stdio", "sse"], default="stdio", help="Transport type (default: stdio)")
    args = parser.parse_args()
    
    mcp.run(transport=args.transport)


def dev() -> None:
    """
    Development function that handles Ctrl+C gracefully.
    This function calls main() but catches KeyboardInterrupt to allow 
    clean exit when user presses Ctrl+C.
    """
    print("mcp server starting", file=sys.stderr)

    # Define signal handler for cleaner exit
    def signal_handler(sig, frame):
        print("\nShutting down mcp server...", file=sys.stderr)
        sys.exit(0)

    # Register the signal handler for SIGINT (Ctrl+C)
    signal.signal(signal.SIGINT, signal_handler)

    try:
        # Run the server with proper exception handling
        main()
    except KeyboardInterrupt:
        print("\nShutting down mcp server...", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)
