import os
import logging
from flask import Flask, request, jsonify, send_file
import json
import requests
import openai
from sqlalchemy import create_engine
import matplotlib
matplotlib.use('Agg')  # Use the non-GUI backend
import matplotlib.pyplot as plt
import pandas as pd
from dotenv import load_dotenv
import io

# Load environment variables
load_dotenv()
XAI_API_KEY = os.getenv("XAI_API_KEY")

if not XAI_API_KEY:
    raise EnvironmentError("XAI_API_KEY is not set in the environment variables.")

# Initialize the XAI API client
client = openai.OpenAI(api_key=XAI_API_KEY, base_url="https://api.x.ai/v1")

# Initialize Flask app
app = Flask(__name__)

# Connect to SQLite database
DATABASE_FILE = "example_database.sqlite"
model = create_engine(f"sqlite:///{DATABASE_FILE}")

# Load the schema from the JSON file
def load_schema(schema_file_path):
    with open(schema_file_path, 'r') as schema_file:
        schema = json.load(schema_file)
    return schema

SCHEMA_FILE_PATH = "schema.json"  # Path to your schema file
schema = load_schema(SCHEMA_FILE_PATH)

# Logging configuration
logging.basicConfig(level=logging.DEBUG)

@app.before_request
def log_request_info():
    # Log request details for debugging
    logging.info(f"Request Headers: {request.headers}")
    logging.info(f"Request Body: {request.json}")

@app.route('/process_query', methods=['POST'])
def process_query_request():
    data = request.json
    query_text = data.get('query')
    output_format = data.get('format', 'text')

    if not query_text:
        return error_response("Missing 'query' parameter")
    if output_format not in ['text', 'table', 'chart']:
        return error_response(f"Unsupported format: {output_format}")

    try:
        # Generate SQL from natural language query
        sql_query = generate_sql(query_text)
        if sql_query.startswith("Error:"):
            return error_response(sql_query)

        # Execute SQL query and fetch results
        with model.connect() as conn:
            result = pd.read_sql(sql_query, conn)

        # Handle different formats
        if output_format == 'chart':
            # Generate chart from result
            chart = generate_chart(result)
            if isinstance(chart, io.BytesIO):
                return send_file(chart, mimetype='image/png')
            else:
                return error_response(chart)

        # Process table or text formats
        return process_result_format(result, output_format)

    except Exception as e:
        logging.error(f"Error in process_query_request: {str(e)}")
        return error_response(f"Error: {str(e)}", 500)

def process_result_format(result, output_format):
    try:
        if output_format == 'text':
            # Return result as plain text
            return jsonify({"result": result.to_string(index=False)})

        elif output_format == 'table':
            # Convert result DataFrame to HTML table
            if isinstance(result, pd.DataFrame):
                return result.to_html(index=False)

        return error_response("Unsupported or invalid output format")

    except Exception as e:
        logging.error(f"Error in process_result_format: {str(e)}")
        return error_response(f"Error: {str(e)}")

def generate_chart(dataframe):
    try:
        if dataframe.empty:
            return "Error: No data available to generate a chart."

        # Assuming the first column is 'x' and second column is 'y'
        x = dataframe.iloc[:, 0]
        y = dataframe.iloc[:, 1]

        # Create a bar chart
        fig, ax = plt.subplots()
        ax.bar(x, y, color='blue')
        ax.set_xlabel("X-axis Label")
        ax.set_ylabel("Y-axis Label")
        ax.set_title("Chart Title")

        # Save chart as an in-memory image
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        plt.close(fig)  # Free memory
        return img

    except Exception as e:
        logging.error(f"Error generating chart: {str(e)}")
        return f"Error: Chart generation failed due to {str(e)}"

def generate_sql(natural_language_query):
    try:
        schema = get_database_schema()
        schema_str = "\n".join(
            f"Table: {table}\n    Columns: {', '.join(columns)}"
            for table, columns in schema.items()
        )

        system_message = (
            f"You are a SQL assistant for a SQLite database. Use the following database schema to write valid SQL queries. "
            f"For date-related operations, use strftime('%Y', column_name) to extract the year. "
            f"Only return the SQL:\n{schema_str}"
        )

        response = client.chat.completions.create(
            model="grok-beta",
            messages=[{
                "role": "system",
                "content": system_message
            }, {
                "role": "user",
                "content": natural_language_query
            }],
            stream=False,
            max_tokens=150,
            temperature=0
        )

        if hasattr(response, 'choices') and len(response.choices) > 0:
            sql_query = response.choices[0].message.content.strip()

            if sql_query.startswith("```"):
                sql_query = "\n".join(sql_query.split("\n")[1:-1]).strip()

            valid_keywords = ["SELECT", "INSERT", "UPDATE", "DELETE"]
            if any(sql_query.upper().startswith(keyword) for keyword in valid_keywords):
                return sql_query

            return f"Error: Generated invalid SQL: {sql_query}"

        return "Error: No valid response choices from the API."

    except Exception as e:
        logging.error(f"Error in SQL generation: {str(e)}")
        return f"Error: SQL generation failed due to {str(e)}"

def get_database_schema():
    schema = {}
    try:
        with model.connect() as conn:
            tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table';", conn)
            for table in tables['name']:
                columns = pd.read_sql(f"PRAGMA table_info({table});", conn)
                schema[table] = columns['name'].tolist()
    except Exception as e:
        logging.error(f"Error fetching database schema: {str(e)}")
    return schema

def error_response(message, status_code=400):
    return jsonify({"error": message}), status_code

if __name__ == '__main__':
    app.run(debug=True)
