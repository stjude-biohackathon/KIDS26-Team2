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

# Load the variables from your .env file
load_dotenv()

def get_dataframe_from_sql(query: str) -> pd.DataFrame:
    """Helper function to execute SQL securely and return a labeled DataFrame."""
    conn_str = os.getenv("AZURE_SQL_CONNECTION_STRING")
    if not conn_str:
        raise ValueError("AZURE_SQL_CONNECTION_STRING is missing from the .env file!")
    
    with pyodbc.connect(conn_str) as conn:
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        
        if not rows:
            return pd.DataFrame() 
            
        columns = [column[0] for column in cursor.description]
        records = [tuple(row) for row in rows]
        
        return pd.DataFrame.from_records(records, columns=columns)


def generate_graph(query: str, plot_type: str, x_column: str, y_column: str = None) -> str:
    try:
        print(f"\n📊 [GRAPH TOOL INITIATED] Plot: {plot_type} | X: {x_column} | Y: {y_column}")
        
        # 1. Fix Claude Hallucinations
        if str(y_column).strip().lower() in ['none', 'null', '']:
            y_column = None

        df = get_dataframe_from_sql(query)
        
        if df.empty:
            return "Error: No data returned from SQL to graph."

        # Validate that Claude guessed the correct column names
        available_cols = list(df.columns)
        if x_column not in available_cols:
            return f"Error: x_column '{x_column}' is missing. Available columns: {available_cols}"
        if y_column and y_column not in available_cols:
            return f"Error: y_column '{y_column}' is missing. Available columns: {available_cols}"

        # --- SMARTER DATA CLEANING ---
        # 1. Drop rows where the data is genuinely missing from the database
        df = df.dropna(subset=[x_column])
        if y_column:
            df = df.dropna(subset=[y_column])

        # 2. Y-axis is almost always numerical, so safely coerce it
        if y_column:
            df[y_column] = pd.to_numeric(df[y_column], errors='coerce')
            
        # 3. For Histograms and Scatter plots, X MUST be numerical. 
        # But for Bar and Box plots, X is usually categorical text (leave it alone!)
        if plot_type in ['histogram', 'scatter']:
            df[x_column] = pd.to_numeric(df[x_column], errors='coerce')

        # 4. Final sweep: drop any rows that failed the numeric coercion
        df = df.dropna(subset=[x_column])
        if y_column:
            df = df.dropna(subset=[y_column])
            
        if df.empty:
            return "Error: After cleaning the data (removing nulls/text), the dataset was empty. Cannot draw graph."
        # -----------------------------

        # Set up the graph canvas
        plt.figure(figsize=(10, 6))
        sns.set_theme(style="whitegrid")

        # Draw the requested plot type
        if plot_type == 'histogram':
            sns.histplot(data=df, x=x_column, kde=True, color="blue")
        elif plot_type == 'bar' and y_column:
            sns.barplot(data=df, x=x_column, y=y_column, palette="viridis")
        elif plot_type == 'scatter' and y_column:
            sns.scatterplot(data=df, x=x_column, y=y_column, alpha=0.6)
        elif plot_type == 'box':
            sns.boxplot(data=df, x=x_column, y=y_column)
        else:
            return f"Error: Invalid plot type '{plot_type}'. If bar or scatter, Y is required."

        plt.title(f"{plot_type.title()} of {x_column} {f'vs {y_column}' if y_column else ''}")
        plt.tight_layout()

        # GUARANTEE the static folder exists before saving
        os.makedirs("static", exist_ok=True)
        
        file_name = f"chart_{uuid.uuid4().hex[:8]}.png"
        file_path = os.path.join("static", file_name)
        plt.savefig(file_path)
        plt.close() 

        # Return the Markdown image string to Claude
        image_url = f"http://localhost:8000/static/{file_name}"
        return f"Successfully created graph! Show this exact markdown to the user: \n\n![{plot_type} chart]({image_url})"

    except Exception as e:
        error_msg = f"Failed to generate graph: {str(e)}"
        print(f"\n🚨 [GRAPH TOOL ERROR] {error_msg}\n")
        return error_msg