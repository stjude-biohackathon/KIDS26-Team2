import os
import pyodbc
import pandas as pd
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.ensemble import (
    RandomForestClassifier, RandomForestRegressor,
    GradientBoostingClassifier, GradientBoostingRegressor
)
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, accuracy_score

def run_biostats_model(query: str, target_column: str, model_type: str) -> str:
    try:
        conn_str = os.environ.get("AZURE_SQL_CONNECTION_STRING")
        if not conn_str:
            return "Error: Database connection string not found."
        
        conn = pyodbc.connect(conn_str)
        df = pd.read_sql(query, conn)
        conn.close()

        # Safety cap to prevent Azure API timeouts on massive MIMIC-IV queries
        if len(df) > 10000:
            df = df.sample(n=10000, random_state=42)

        if target_column not in df.columns:
            return f"Error: Target column '{target_column}' not found."

        df = df.dropna()
        numeric_df = df.select_dtypes(include=['number'])
        
        if target_column not in numeric_df.columns:
            return f"Error: Target '{target_column}' must be numeric (use 1/0 for classification)."

        X = numeric_df.drop(columns=[target_column])
        y = numeric_df[target_column]

        if X.empty:
            return "Error: No numeric features available."

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        results = []
        model_type_clean = model_type.lower().strip()
        
        # --- MODEL SELECTION ROUTER ---
        if model_type_clean == "logistic_regression":
            model = LogisticRegression(max_iter=1000)
            model.fit(X_scaled, y)
            results.append(f"Model: Logistic Regression | Accuracy: {accuracy_score(y, model.predict(X_scaled)):.4f}")
            importances = model.coef_[0]
            
        elif model_type_clean == "random_forest_classifier":
            model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
            model.fit(X_scaled, y)
            results.append(f"Model: Random Forest Classifier | Accuracy: {accuracy_score(y, model.predict(X_scaled)):.4f}")
            importances = model.feature_importances_
            
        elif model_type_clean == "gradient_boosting_classifier":
            model = GradientBoostingClassifier(n_estimators=100, random_state=42)
            model.fit(X_scaled, y)
            results.append(f"Model: Gradient Boosting Classifier | Accuracy: {accuracy_score(y, model.predict(X_scaled)):.4f}")
            importances = model.feature_importances_
            
        elif model_type_clean == "linear_regression":
            model = LinearRegression()
            model.fit(X_scaled, y)
            results.append(f"Model: Linear Regression | R-squared: {r2_score(y, model.predict(X_scaled)):.4f}")
            importances = model.coef_
            
        elif model_type_clean == "random_forest_regressor":
            model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
            model.fit(X_scaled, y)
            results.append(f"Model: Random Forest Regressor | R-squared: {r2_score(y, model.predict(X_scaled)):.4f}")
            importances = model.feature_importances_
            
        elif model_type_clean == "gradient_boosting_regressor":
            model = GradientBoostingRegressor(n_estimators=100, random_state=42)
            model.fit(X_scaled, y)
            results.append(f"Model: Gradient Boosting Regressor | R-squared: {r2_score(y, model.predict(X_scaled)):.4f}")
            importances = model.feature_importances_
            
        else:
            return f"Error: Unknown model_type '{model_type}'."

        # --- EXTRACT FEATURE WEIGHTS ---
        results.append("\nFeature Importance / Coefficients:")
        # Sort features by absolute importance for readability
        feature_weights = sorted(zip(X.columns, importances), key=lambda x: abs(x[1]), reverse=True)
        
        for feature, weight in feature_weights:
            results.append(f"- {feature}: {weight:.4f}")

        return "\n".join(results)

    except Exception as e:
        return f"Model execution failed: {str(e)}"