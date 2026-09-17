import os
import pyodbc
import pandas as pd
from scipy import stats
from dotenv import load_dotenv

# Load the variables from your .env file
load_dotenv()

def get_dataframe_from_sql(query: str) -> pd.DataFrame:
    """Helper function to execute SQL securely and return a labeled DataFrame."""
    
    # 1. Grab your full connection string directly from .env
    conn_str = os.getenv("AZURE_SQL_CONNECTION_STRING")
    
    if not conn_str:
        raise ValueError("AZURE_SQL_CONNECTION_STRING is missing from the .env file!")
    
    # 2. Connect and execute using the exact string Azure provided
    with pyodbc.connect(conn_str) as conn:
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        
        if not rows:
            return pd.DataFrame() # Return empty if no data
            
        # 3. Extract column names from the cursor description
        columns = [column[0] for column in cursor.description]
        
        # 4. Convert pyodbc Row objects to standard tuples for Pandas compatibility
        records = [tuple(row) for row in rows]
        
        # 5. Bind the rows and columns perfectly into Pandas
        return pd.DataFrame.from_records(records, columns=columns)


def generate_descriptive_stats(query: str, target_column: str) -> str:
    """
    Executes a SQL query, loads it into Pandas, and returns a statistical summary.
    """
    try:
        # Use our new helper to fetch the data
        df = get_dataframe_from_sql(query)
        
        # Check if empty or if the agent guessed the wrong column name
        if df.empty or target_column not in df.columns:
            available = list(df.columns) if not df.empty else "None"
            return f"Error: No data found or column '{target_column}' is missing. Available columns: {available}"

        # Clean the data (force to numbers, drop blanks/text)
        df[target_column] = pd.to_numeric(df[target_column], errors='coerce')
        clean_df = df.dropna(subset=[target_column])
        
        if clean_df.empty:
            return f"Error: No valid numeric data could be extracted from column '{target_column}'."
        
        # Run the statistics
        summary = clean_df[target_column].describe()
        
        # Format as a clean Markdown table for Claude
        report = f"### Statistical Report: {target_column}\n\n"
        report += summary.to_frame().to_markdown()
        
        return report

    except Exception as e:
        return f"Statistical calculation failed: {str(e)}"