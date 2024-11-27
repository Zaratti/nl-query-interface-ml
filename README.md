# nl-query-interface-ml
Developing a script that exposes an API endpoint where admins can input natural language queries (e.g., “Show me the total sales for last month”). The NLP model processes the input, generates a safe SQL query, runs it on the connected database, and returns the response in text, chart, or table formats based on the nature of the data.

## Installation Documentation(Schema and SQL Refining)
- After setting up the necessary library's in the Flask app: (I used VS Code). I loaded the environment variables and set up connection to the database using their supported parameters.
    - **Natural Language to SQL**: The interface accepts natural language input, send that natural language query to xA.I, lets xA.I know it is the system and how to generate SQL queries from natural language inputs using a schema that xAI's model work with to genrate SQL for the database.
    - **Dynamic Schema Usage**: Used json, to set a schema that clearly outlines the column names, data type and description structure of the database to enhance SQL generation accuracy.
    - **Database Integration**: Connects to a SQLite database to execute generated SQL queries from xA.I.
    - **Error Handling**: I used try and exceptions to return detailed error messages for invalid inputs or unsupported formats, and handle such errors.
    - **Logging**: For easier debugging processes, I used logging within the exceptions for comprehensive request and error logginh.
    - **Result Formats**: Output results are in:
        - **Text**: This shows plain text representation of query results.
        - **Table**: This shows HTML table for structured data.
        - **Chart**: This shows Visual bar charts based on query results.

## Usage/Setup
- Clone the Repository
- Install Dependencies
- Configure Environment Variables
- Prepare the Database
- Run the Application
- Test the API using Postman to test the query endpoint and visualize your result.


## Notes
- Ensure the xAI API key(or whatever model you decide to use) has sufficient quota to handle requests, this will help you handle RateLimitErrors.
- Update the database file(I used sqlite, your database could be different) and schema(that is, an outlined description of the structure of your connected database) as needed to match your application.

## Example Queries
- Text:
 ```{
        "query": "List the last five users",
        "format": "text"
    }
```

- Table:
 ```{
    "query": "Show the number of users who signed up each year",
    "format": "table"
    }
 ```

- Chart:
 ```{
    "query": "Visualize the number of users who signed up each year",
    "format": "chart"
    }
 ```
