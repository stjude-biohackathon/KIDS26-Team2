import os
import pyodbc
import pandas as pd
import uuid
from dotenv import load_dotenv

load_dotenv()

def get_dataframe_from_sql(query: str) -> pd.DataFrame:
    """Executes SQL securely and returns a DataFrame."""
    conn_str = os.getenv("AZURE_SQL_CONNECTION_STRING")
    if not conn_str:
        raise ValueError("AZURE_SQL_CONNECTION_STRING is missing!")
    
    with pyodbc.connect(conn_str) as conn:
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        if not rows: return pd.DataFrame() 
        columns = [column[0] for column in cursor.description]
        records = [tuple(row) for row in rows]
        return pd.DataFrame.from_records(records, columns=columns)

def export_to_csv(query: str, dataset_name: str = "clinical_data") -> str:
    """
    Tool for the LLM to export SQL data to a CSV file.
    dataset_name: A short, descriptive name for the file (e.g., 'patient_vitals').
    """
    try:
        print(f"\n💾 [EXPORT TOOL] Extracting data for: {dataset_name}")
        
        df = get_dataframe_from_sql(query)
        if df.empty:
            return "Error: No data returned from SQL to export."

        # Save the CSV to the static folder
        os.makedirs("static", exist_ok=True)
        file_name = f"{dataset_name.replace(' ', '_')}_{uuid.uuid4().hex[:8]}.csv"
        file_path = os.path.join("static", file_name)
        
        df.to_csv(file_path, index=False)

        # Pull the backend URL (uses localhost for local Mac testing)
        backend_url = os.getenv("BACKEND_PUBLIC_URL", "http://localhost:8000")
        
        # The LLM outputs a standard Markdown link
        return f"Successfully exported data! Show this exact markdown link to the user: \n\n[📥 Download {dataset_name}.csv]({backend_url}/static/{file_name})"

    except Exception as e:
        return f"Failed to export data: {str(e)}"