from flask import Flask, request, jsonify
import pandas as pd
import os
import pickle
import sqlite3
from pandas.api.types import is_numeric_dtype
from llm_query_generator import get_query_from_llm, clean_query
from flask_cors import CORS


app = Flask(__name__)
CORS(app)

# Global variables
dataframes = {}
schema = {}
SERIALIZED_FOLDER = "serialized_data"
DB_FILE = "joined_data.db"
ROOT_TABLE = "orders"
FOLDER_PATH = "/Users/noahkhan/StartupWork/tria/triaData"  # Replace with your folder path


def load_or_serialize_csv_files(folder_path):
    """
    Loads CSV files only once by saving them as serialized files.
    If serialized files exist, it loads from them instead.
    """
    global dataframes

    os.makedirs(SERIALIZED_FOLDER, exist_ok=True)

    for file in os.listdir(folder_path):
        if file.endswith(".csv"):
            df_name = file.replace(".csv", "")
            serialized_path = os.path.join(SERIALIZED_FOLDER, f"{df_name}.pkl")

            if os.path.exists(serialized_path):
                with open(serialized_path, "rb") as f:
                    dataframes[df_name] = pickle.load(f)
            else:
                df = pd.read_csv(os.path.join(folder_path, file))
                dataframes[df_name] = df
                with open(serialized_path, "wb") as f:
                    pickle.dump(df, f)

    print("DataFrames loaded successfully.")
    return dataframes


def discover_relationships():
    """
    Identifies potential relationships between DataFrames based on common columns.
    Stores the relationships in a schema dictionary.
    """
    global schema
    schema = {df_name: {"columns": df.columns.tolist(), "relationships": []} for df_name, df in dataframes.items()}

    for df1_name, df1 in dataframes.items():
        for df2_name, df2 in dataframes.items():
            if df1_name != df2_name:
                common_columns = set(df1.columns).intersection(df2.columns)
                for column in common_columns:
                    if is_numeric_dtype(df1[column]) and is_numeric_dtype(df2[column]):
                        if column not in ["Latitude", "Longitude"]:
                            schema[df1_name]["relationships"].append({"related_table": df2_name, "on_column": column})

    print("Relationships discovered.")
    return schema


def validate_relationships():
    """
    Validate relationships to ensure columns exist and are properly formatted for joining.
    """
    for table, details in schema.items():
        for relationship in details["relationships"][:]:  # Use slicing to safely modify while iterating
            related_table = relationship["related_table"]
            on_column = relationship["on_column"]

            if on_column not in dataframes[table].columns:
                details["relationships"].remove(relationship)
            elif on_column not in dataframes[related_table].columns:
                details["relationships"].remove(relationship)
            elif dataframes[table][on_column].dtype != dataframes[related_table][on_column].dtype:
                details["relationships"].remove(relationship)

    print("Relationships validated.")


def join_tables(root_table, schema):
    """
    Automates the joining of tables based on the schema relationships.
    """
    joined_df = dataframes[root_table].copy()  # Start with the root table
    visited_tables = {root_table}  # Keep track of visited tables

    def recursive_join(current_table, joined_df):
        for relationship in schema[current_table]["relationships"]:
            related_table = relationship["related_table"]
            on_column = relationship["on_column"]

            if related_table not in visited_tables:
                joined_df = pd.merge(joined_df, dataframes[related_table], on=on_column, how="left", suffixes=("", "_dup"))
                visited_tables.add(related_table)
                joined_df = recursive_join(related_table, joined_df)

        return joined_df

    return recursive_join(root_table, joined_df)


def setup_data():
    """
    Handles the initial data loading, relationship discovery, and database setup.
    """
    print("Initializing data...")
    load_or_serialize_csv_files(FOLDER_PATH)
    discover_relationships()
    validate_relationships()

    joined_data = join_tables(ROOT_TABLE, schema)

    # Save joined table to SQLite
    conn = sqlite3.connect(DB_FILE)
    joined_data.to_sql("joined_table", conn, if_exists="replace", index=False)
    conn.close()
    print("Database initialized.")


@app.route('/query', methods=['POST'])
def handle_query():
    """
    Single endpoint to accept a user prompt, generate a query, and return results.
    """
    user_query = request.json.get("query")
    if not user_query:
        return jsonify({"error": "Query parameter is required"}), 400

    try:
        # Generate SQL query using the LLM
        generated_query = get_query_from_llm(user_query, schema)

        # Clean the query
        cleaned_query = clean_query(generated_query)

        if not cleaned_query.strip().lower().startswith("select"):
            return jsonify({"error": "Invalid SQL query generated"}), 400

        # Execute the query
        conn = sqlite3.connect(DB_FILE)
        results = pd.read_sql_query(cleaned_query, conn)
        conn.close()

        # Return the results as JSON
        return jsonify(results.to_dict(orient="records"))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    setup_data()  # Initialize data before starting the server
    app.run(debug=True)
