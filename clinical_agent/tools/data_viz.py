import os
import pyodbc
import pandas as pd
import matplotlib
import seaborn as sns
import matplotlib.pyplot as plt
import uuid
from dotenv import load_dotenv

# Force background rendering to prevent server crashes
matplotlib.use('Agg') 
load_dotenv()

def get_dataframe_from_sql(query: str) -> pd.DataFrame:
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

def generate_graph(query: str, plot_type: str, x_column: str, y_column: str = None) -> str:
    try:
        print(f"\n📊 [GRAPH TOOL] Plot: {plot_type} | X: {x_column} | Y: {y_column}")
        
        if str(y_column).strip().lower() in ['none', 'null', '']: y_column = None
        df = get_dataframe_from_sql(query)
        if df.empty: return "Error: No data returned."

        df = df.dropna(subset=[x_column])
        if y_column:
            df = df.dropna(subset=[y_column])
            df[y_column] = pd.to_numeric(df[y_column], errors='coerce')
            
        if plot_type in ['histogram', 'scatter']:
            df[x_column] = pd.to_numeric(df[x_column], errors='coerce')

        df = df.dropna(subset=[x_column])
        if y_column: df = df.dropna(subset=[y_column])
        if df.empty: return "Error: Dataset empty after cleaning."

        plt.figure(figsize=(10, 6))
        sns.set_theme(style="whitegrid")

        if plot_type == 'histogram': sns.histplot(data=df, x=x_column, kde=True, color="blue")
        elif plot_type == 'bar' and y_column: sns.barplot(data=df, x=x_column, y=y_column, palette="viridis")
        elif plot_type == 'scatter' and y_column: sns.scatterplot(data=df, x=x_column, y=y_column, alpha=0.6)
        elif plot_type == 'box': sns.boxplot(data=df, x=x_column, y=y_column)
        else: return f"Error: Invalid plot type '{plot_type}'."

        plt.title(f"{plot_type.title()} of {x_column} {f'vs {y_column}' if y_column else ''}")
        plt.tight_layout()

        # --- OPTION 2: SAVE TO DISK ---
        os.makedirs("static", exist_ok=True)
        file_name = f"chart_{uuid.uuid4().hex[:8]}.png"
        plt.savefig(os.path.join("static", file_name))
        plt.close() 

        # Pull the backend URL (default to localhost for Mac testing)
        backend_url = os.getenv("BACKEND_PUBLIC_URL", "http://localhost:8000")
        
        # The LLM only has to type this tiny string!
        return f"Successfully created graph! Show this exact markdown: \n\n![{plot_type} chart]({backend_url}/static/{file_name})"

    except Exception as e:
        return f"Failed to generate graph: {str(e)}"