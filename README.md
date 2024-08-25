# 🐠 Babelfish.db
*Your universal translator for human-to-database communication - making data speak your language!*

---
## Overview

**Babelfish.db** is an intelligent database assistant designed to facilitate natural language interactions with both SQL and NoSQL databases. It enables users to query their databases using plain English and generates responses in a conversational manner. Additionally, it can generate detailed PDF reports of the interactions.

Try it out for pubically hosted databases: https://babelfish-db.streamlit.app/

## Features

- **Natural Language Querying**: Allows users to ask questions in natural language.
- **SQL Database Support**: Connects to MySQL databases and automatically generates SQL queries based on user questions.
- **NoSQL Database Support**: Connects to MongoDB databases and constructs MongoDB aggregation pipelines based on user queries.
- **PDF Report Generation**: Creates detailed reports of conversations in PDF format.

![Picture1](https://github.com/user-attachments/assets/92f85b12-4f74-43de-8521-d511316d3827)


## Technology Stack

- **Streamlit**: For building the web interface.
- **LangChain**: For processing natural language queries.
- **Groq**: For leveraging high-speed & accurate text generation capabilities with LLMs (large language models) to assist with query generation and responses.
- **MySQL**: For SQL database connectivity.
- **MongoDB**: For NoSQL database connectivity.
- **FPDF**: For generating PDF reports.

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/whonehuljain/Babelfish.db
    cd Babelfish.db
    ```

2. Create a virtual environment and activate it (Optional):
    ```sh
    python -m venv env
    source env/Scripts/activate
    ```

3. Install the dependencies:
    ```sh
    pip install -r requirements.txt
    ```

## Usage

1. **Launch the Application**:
    ```sh
    streamlit run main.py
    ```
    *Remember to replace your groq api key in main.py before launching the app.*

2. **Connect to a Database**:
    - Use the sidebar to select the database type (MySQL or MongoDB).
    - Enter the necessary connection details and click "Connect".

3. **Interact with Your Database**:
    - Type your questions in the chat input box.
    - The assistant will generate and run the appropriate queries, then respond in natural language.

4. **Generate PDF Reports**:
    - After interacting with the assistant, click the "Generate Report" button to create a PDF report of the conversation.
    - Download the PDF using the provided download button.

## Technical Details

### 1. SQL Integration
- **Schema Retrieval**: Connect to the SQL database and retrieve the table schema.
- **Query Generation**: Pass the schema and user query to the LLM to generate the SQL query.
- **Execution and Response**: Execute the SQL query and pass the results along with the user query to the LLM for a natural language response.

### 2. MongoDB Integration
- **Document Retrieval**: Query the MongoDB collection to retrieve two representative documents.
- **Schema Inference**: Pass these documents to the LLM to infer the database schema.
- **Aggregation Pipeline**: Use the inferred schema to generate an aggregation pipeline query.
- **Execution and Response**: Execute the aggregation pipeline and pass the results and user query to the LLM for a natural language response.

### 3. PDF Report Generation
- **Capture the Conversation**: Capture the conversation history and format it for PDF output when the user presses the “Generate Report” button.
- **Download Option**: Provide a “Download” option for users to save the conversation history as a PDF file.

## Examples

### MySQL Query Example

- **User**: How many employees are there in the company?
- **Assistant**: There are 150 employees in the company.

### MongoDB Query Example

- **User**: List all the products in the 'electronics' category.
- **Assistant**: Here are the products in the 'electronics' category: ...

## Troubleshooting

- **Connection Issues**: Ensure that the database credentials are correct and that the database server is accessible.
- **Query Errors**: Check the schema and the examples generated to ensure that the queries are being formed correctly.

## License

This project is licensed under the MIT License.
