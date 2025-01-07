import os
from openai import OpenAI
from dotenv import load_dotenv
import sqlite3
import pandas as pd

# Load environment variables from .env file
load_dotenv()

# Initialize the OpenAI client
api_key = os.getenv("OPENAI_API_KEY")  # Securely fetch the API key
if not api_key:
    api_key = "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"  # Replace with your OpenAI API key
    if not api_key:
        raise ValueError("OpenAI API key is not set.")

client = OpenAI(api_key=api_key)

def generate_prompt(user_query, schema_text):
    """
    Creates a detailed prompt to send to the LLM, leveraging schema information.
    """
    return f"""
    Given the following database schema for a single joined table containing all data:
    {schema_text}

    Generate a SQL query to answer this request: '{user_query}'

    CRITICAL REQUIREMENTS:
    1. Return ONLY the exact SQL query with NO explanations
    2. Use ONLY the table name 'joined_table'
    3. Do not include words like 'Query:', 'SQL:', or any other prefixes
    4. Include complete HAVING clause with these exact conditions:
       ReliabilityScore < 0.9 OR 
       AVG(AverageTimeToShipment) > 10 OR 
       (SUM(LateDelivery) * 100.0 / COUNT(*)) > 20

    Copy and complete this exact query structure:
    SELECT 
        SupplierID,
        SupplierName,
        ReliabilityScore,
        AVG(AverageTimeToShipment) as AvgShipTime,
        SUM(LateDelivery) * 100.0 / COUNT(*) as LateDeliveryPercentage
    FROM joined_table 
    GROUP BY 
        SupplierID,
        SupplierName,
        ReliabilityScore
    HAVING 
        ReliabilityScore < 0.9 
        OR AVG(AverageTimeToShipment) > 10 
        OR (SUM(LateDelivery) * 100.0 / COUNT(*)) > 20;
    """

def clean_query(raw_query):
    """
    Extracts only the SQL query from the response, removing any explanations or markdown.
    """
    # Remove any markdown
    query = raw_query.replace('```sql', '').replace('```', '')
    
    # Find the first SELECT statement
    start_idx = query.upper().find('SELECT')
    if start_idx == -1:
        return ""
    
    # Find the last semicolon
    end_idx = query.rfind(';')
    if end_idx == -1:
        end_idx = len(query)
    
    # Extract just the SQL query
    query = query[start_idx:end_idx + 1]
    
    # Clean up any remaining issues
    query = query.strip()
    
    return query

def get_query_from_llm(user_query, schema):
    """
    Sends the user's query and schema information to the LLM to generate a SQL query.
    """
    # Convert schema to a formatted string for the prompt
    schema_text = "\n".join(
        [f"Table: {table}, Columns: {', '.join(details['columns'])}" for table, details in schema.items()]
    )

    # Generate the prompt
    prompt = generate_prompt(user_query, schema_text)

    # Send the prompt to the OpenAI API
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a data analyst and SQL expert."},
            {"role": "user", "content": prompt}
        ]
    )

    # Extract and clean the SQL query
    raw_query = response.choices[0].message.content.strip()
    cleaned_query = clean_query(raw_query)

    return cleaned_query

def refine_query_with_context(user_query, initial_analysis):
    """
    Refines the LLM's generated query by providing additional context or explanations for optimization.
    """
    structured_prompt = f"""
    Based on the following user's query and the initial query you generated, refine it for clarity and optimization.

    User Query:
    '{user_query}'

    Initial Query:
    {initial_analysis}

    Task:
    - Simplify or enhance the query where possible.
    - Ensure all relationships in the schema are leveraged correctly.
    - Verify the query's ability to handle edge cases such as missing data, duplicates, or ambiguous fields.
    - Return only the refined query.

    Refined Query:
    """

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an SQL optimization expert."},
            {"role": "user", "content": structured_prompt}
        ]
    )

    return clean_query(response.choices[0].message.content.strip())

def analyze_results(results_df, user_query):
    """
    Generates a detailed analysis of the query results using the LLM.
    """
    # Convert results to a string format for the prompt
    results_str = results_df.to_string()
    
    analysis_prompt = f"""
    Analyze these supplier performance results:
    {results_str}

    Original Query Request: {user_query}

    Provide a detailed analysis including:
    1. Root Cause Analysis:
       - Identify patterns in underperformance
       - Highlight critical metrics and thresholds exceeded
       - Suggest potential underlying causes

    2. Descriptive Analysis:
       - Summarize key findings
       - Compare performance across suppliers
       - Highlight most significant issues
       - Quantify the impact of poor performance

    3. Recommendations:
       - Suggest specific improvements
       - Prioritize which suppliers need immediate attention
       - Propose monitoring metrics

    Format the analysis in clear sections with bullet points where appropriate.
    """

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a supply chain analytics expert."},
            {"role": "user", "content": analysis_prompt}
        ]
    )

    return response.choices[0].message.content.strip()
