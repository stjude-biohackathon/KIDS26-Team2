import os
import pyodbc
from dotenv import load_dotenv

load_dotenv()

def execute_sql_query(query: str) -> str:
    """Executes a strictly read-only T-SQL query on Azure SQL."""
    # Safety guardrail: reject mutating commands
    forbidden = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE"]
    if any(keyword in query.upper() for keyword in forbidden):
        return "ERROR: Non-SELECT statements are strictly prohibited."
        
    try:
        conn = pyodbc.connect(os.getenv("AZURE_SQL_CONNECTION_STRING"))
        cursor = conn.cursor()
        cursor.execute(query)
        
        # Extract column names and fetch limited rows for token safety
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchmany(15) 
        results = [dict(zip(columns, row)) for row in rows]
        conn.close()
        
        return str(results) if results else "No records found in the database."
    except Exception as e:
        return f"SQL Execution Error: {str(e)}"