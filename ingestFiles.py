import pandas as pd
import os
import pickle
from pandas.api.types import is_numeric_dtype
import sqlite3
from llm_query_generator import get_query_from_llm

# Global variables
dataframes = {}
schema = {}

SERIALIZED_FOLDER = "serialized_data"

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

    # Debugging: Display the loaded dataframes and their columns
    for df_name, df in dataframes.items():
        print(f"Loaded DataFrame: {df_name}")
        print(df.head())
        print(df.dtypes)

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
                        # Exclude relationships based on Latitude and Longitude
                        if column not in ["Latitude", "Longitude"]:
                            schema[df1_name]["relationships"].append({"related_table": df2_name, "on_column": column})

    # Debugging: Display discovered relationships
    for table, details in schema.items():
        print(f"\nSchema for Table: {table}")
        print(f"Columns: {details['columns']}")
        for relationship in details["relationships"]:
            print(f"Related Table: {relationship['related_table']}, On Column: {relationship['on_column']}")

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
                print(f"Warning: Column '{on_column}' not found in table {table}. Removing relationship.")
                details["relationships"].remove(relationship)
            elif on_column not in dataframes[related_table].columns:
                print(f"Warning: Column '{on_column}' not found in table {related_table}. Removing relationship.")
                details["relationships"].remove(relationship)
            elif dataframes[table][on_column].dtype != dataframes[related_table][on_column].dtype:
                print(f"Warning: Column '{on_column}' type mismatch between '{table}' and '{related_table}'. Removing relationship.")
                details["relationships"].remove(relationship)
            else:
                print(f"Validated relationship: {table} -> {related_table} on {on_column}")

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
                try:
                    # Debug column names before join
                    print(f"Columns in {current_table} before join: {joined_df.columns}")
                    print(f"Columns in {related_table}: {dataframes[related_table].columns}")

                    # Perform the join
                    print(f"Joining {current_table} with {related_table} on {on_column}")
                    joined_df = pd.merge(joined_df, dataframes[related_table], on=on_column, how="left", suffixes=("", "_dup"))
                    visited_tables.add(related_table)

                    # Recursively join further
                    joined_df = recursive_join(related_table, joined_df)
                except KeyError as e:
                    print(f"KeyError during join: {e}")
                    print(f"Check if column '{on_column}' exists in both '{current_table}' and '{related_table}'.")
                except Exception as e:
                    print(f"Unexpected error during join between '{current_table}' and '{related_table}' on '{on_column}': {e}")

        return joined_df

    return recursive_join(root_table, joined_df)

def clean_query(raw_query):
    """
    Cleans the raw SQL query by removing any non-SQL text.
    """
    lines = raw_query.splitlines()
    sql_lines = [line.strip() for line in lines if not line.startswith("```")]
    return " ".join(sql_lines).strip()

def validate_and_run_query(query, schema):
    """
    Validates the generated SQL query against the schema and executes it.
    """
    conn = sqlite3.connect("joined_data.db")
    try:
        # Validate table and column references in the query
        missing_references = []
        for table in schema:
            for column in schema[table]["columns"]:
                if f"{table}.{column}" in query or f"{column}" in query:
                    break
            else:
                missing_references.append(table)

        if missing_references:
            print(f"Warning: Query references tables/columns not present in the schema: {missing_references}")

        # Execute the query
        return pd.read_sql_query(query, conn)
    except Exception as e:
        print(f"Error executing query: {e}")
        return None
    finally:
        conn.close()

if __name__ == "__main__":
    folder_path = "/Users/noahkhan/StartupWork/tria/triaData"  # Replace with your folder path

    # Step 1: Load and prepare data
    dataframes = load_or_serialize_csv_files(folder_path)

    # Step 2: Discover and validate relationships
    schema = discover_relationships()
    validate_relationships()

    # Step 3: Join tables and save to SQLite
    root_table = "orders"
    joined_data = join_tables(root_table, schema)
    conn = sqlite3.connect("joined_data.db")
    joined_data.to_sql("joined_table", conn, if_exists="replace", index=False)

    # Debugging: Display joined table schema
    schema_info = pd.read_sql_query("PRAGMA table_info(joined_table);", conn)
    print("Joined Table Schema:")
    print(schema_info)
    conn.close()

    # Step 4: Generate a query using LLM
    print("Schema passed to LLM:")
    print(schema)

    user_query = input("Enter your query in plain English: ")
    generated_query = get_query_from_llm(user_query, schema)
    print(f"Generated SQL Query (Raw):\n{generated_query}")

    if not generated_query.strip():
        print("LLM failed to generate a query. Falling back to template.")
        generated_query = "SELECT SupplierID, SupplierName, AVG(ReliabilityScore) AS AvgScore FROM suppliers WHERE ReliabilityScore < 0.9 GROUP BY SupplierID, SupplierName"

    # Step 5: Clean and execute the query
    cleaned_query = clean_query(generated_query)
    print(f"Cleaned SQL Query:\n{cleaned_query}")

    if not cleaned_query.strip().lower().startswith("select"):
        print(f"Invalid query detected: {cleaned_query}")
        raise ValueError("Generated query is not valid SQL.")

    results = validate_and_run_query(cleaned_query, schema)
    if results is not None:
        print("Query Results:")
        print(results)
    else:
        print("No results returned. Please check the query.")
