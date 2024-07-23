import streamlit as st
import os
import re
from fpdf import FPDF
import io
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import OperationFailure
from mysql.connector import ProgrammingError
import json
from groq import Groq
from langchain_community.agents import *
from langchain_community.utilities import SQLDatabase
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq


GROQ_API_KEY = "groq_ttdb_api_key"
output_parser = StrOutputParser()
llm = ChatGroq(model="llama3-70b-8192",api_key=GROQ_API_KEY)
groq_client = Groq(api_key=GROQ_API_KEY)

db = None
sql_schema = None

mongo_schema = None
mongo_example = None

def connect_mysql(username, password, host, schema_name):
    global db_user, db_password, db_host, db_name   
    db_user = username
    db_password = password
    db_host = host
    db_name = schema_name
    db = SQLDatabase.from_uri(f"mysql+mysqlconnector://{db_user}:{db_password}@{db_host}/{db_name}")
    return db

def connect_mongodb(username,password,hostname,db_name,collection_name):
    mongo_uri = f"mongodb://{username}:{password}@{hostname}/"
    client = MongoClient(mongo_uri)
    db_name = db_name
    mongo_db = client[db_name]
    collection = mongo_db[collection_name]


    documents_cursor = collection.find().limit(2)
    documents = [doc for doc in documents_cursor]

    doc_str = str(documents)

    mongo_schema = generate_schema_mongo(doc_str)
    mongo_example = generate_example_mongo(mongo_schema)

    st.session_state.mongo_schema = mongo_schema
    st.session_state.mongo_example = mongo_example

    return collection






#sql
def generate_sql_query(schema_sql,user_question):
    template = """You are a helpful mysql database agent named "Babelfish.db".
    Based on the table schema below, write a SQL query that would answer the user's question:
    {schema}
    Question: {question}

    Return me just the sql query in a single line and no other additional info, without explaining anything. 
    """

    prompt = ChatPromptTemplate.from_template(template)

    sql_chain = prompt | llm | output_parser

    sql_query=sql_chain.invoke({"schema":schema_sql,"question":user_question})
    return sql_query

def run_sql_query(sql_db, sql_query):
    sql_ans=sql_db.run(sql_query)
    return sql_ans

def final_sql_ans(user_question, sql_query, sql_ans):
    template = """You are a helpful mysql database agent, named "Babelfish.db"!
    Based on the table schema below, question, sql query, and sql response, write a natural language response:
    
    {schema}
    
    Question: {question}
    Sql query: {query}
    SQL Response: {response}

    Tell this result to the user in natural language. Just provide the answer untill not asked for the query!
    Keep the response small and to the point"""

    prompt_response = ChatPromptTemplate.from_template(template)

    full_chain = prompt_response | llm | output_parser

    final_ans = full_chain.invoke({"schema":sql_schema,"question":user_question,"query":sql_query,"response":sql_ans})
    return final_ans


#mongo
def generate_schema_mongo(doc_str):
    schema_generating_prompt = """You are a nosql mongo database engineer with 10+ years of experience. 
    I will provide you with the some documets of my mongodb collection for example.
    Your task is to create a table schema for my nosql mongodb database like:
        {
            "_id": {
                "type": "string",
                "description": "Unique identifier for the document"
            },
            "title": {
                "type": "string",
                "description": "Title of the book"
            },
            "isbn": {
                "type": "string",
                "description": "International Standard Book Number"
            },
            "pageCount": {
                "type": "integer",
                "description": "Number of pages in the book"
            },
            "publishedDate": {
                "type": "date",
                "description": "Date the book was published"
            },
            "thumbnailUrl": {
                "type": "string",
                "description": "URL of the book's thumbnail image"
            },
            "shortDescription": {
                "type": "string",
                "description": "Short summary of the book"
            },
            "longDescription": {
                "type": "string",
                "description": "Long summary of the book"
            },
            "status": {
                "type": "string",
                "description": "Status of the book (e.g. PUBLISH, DRAFT, etc.)"
            },
            "authors": {
                "type": "array",
                "description": "List of authors of the book",
                "items": {
                    "type": "string"
                }
            },
            "categories": {
                "type": "array",
                "description": "List of categories the book belongs to",
                "items": {
                    "type": "string"
                }
            }
        }

    Here are 2 documents of my nosql mongodb collection:
    """ + doc_str + """ 
    Note: You have to just return the table schema and description in the given format nothing else. Don't return any additional text with it.
    No additional text such as 'Here is the table schema for the provided MongoDB collection' """

    schema_groq_chat = groq_client.chat.completions.create(
        model="mixtral-8x7b-32768",
        messages=[
            {
                "role": "user",
                "content": schema_generating_prompt
            }
        ],
        temperature=0,
        max_tokens=32768,
    )
    schema = schema_groq_chat.choices[0].message.content
    schema_str = schema.encode('unicode-escape').decode()
    return schema_str

def generate_example_mongo(schema_mongo):
    example_generating_prompt = """ You are an expert nosql mongodb engineer with 10+ year of experience. 
    I will provide you with the table schema of my nosql mongodb database and also 
    I will provide you an example of a mongodb aggregation pipeline output with the input question. 
    Your Task is to generate a similar kind of example of the mongodb aggregation pipeline for the table schema that i have provided you in the format of the example given.
    Here is the example:
    Input: name of departments where number of employees is greater than 1000
    Output: [
                    {
                        "$match": {"departments.employees": {"$gt": 1000}}
                    },
                    {
                        "$project": {
                            "departments": {
                                "$filter": {
                                    "input": "$departments",
                                    "as": "dept",
                                    "cond": {"$gt": ["$$dept.employees", 1000]}
                                }
                            }
                        }
                    }
                ]
    Here is the table schema and description of my mongodb database:
    """ + schema_mongo + """ 
    Note: You have to just return the similar kind of example for the table schema that i have given you nothing else.
    Don't return any additional text with it.
    No additional text such as 'Here is an example of a MongoDB aggregation pipeline based on the provided table schema'
    Just give the output as:
    Input: 'Question'
    Output: MongoDB aggregation pipeline
    """
    example_groq_chat = groq_client.chat.completions.create(
        model="mixtral-8x7b-32768",
        messages=[
            {
                "role": "user",
                "content": example_generating_prompt
            }
        ],
        temperature=0,
        max_tokens=32768,
    )
    example = example_groq_chat.choices[0].message.content
    example_str = json.dumps(example)
    return example_str

def generate_mongo_query(mongo_schema,mongo_example,user_question):
    mongo_query_prompt = """
    You are named "Babelfish.db", an expert in crafting NoSQL queries for MongoDB with 10 years of experience, particularly in MongoDB. 
    I will provide you with the table schema and description in a specified format. 
    Your task is to read the user_question, which will adhere to certain guidelines or formats, and create a NOSQL MongoDb pipeline accordingly.
    Table schema:
    """ + mongo_schema + """
    Here are some example:
    """ + mongo_example + """

    very important: only return the result query in a list and not json

    Note: You have to just return the query nothing else. Don't return any additional text with the query.
    Input: """ + user_question + """ 
    Note: You have to just return one single query in simple string nothing else.
    Don't return any additional text with it.
    No additional text such as 'Here is the query based on the provided table schema' in the starting as well as 
    no additional information like 'The above pipeline will return the... ' """
    mongo_query_groq = groq_client.chat.completions.create(
        model="mixtral-8x7b-32768",
        messages=[
            {
                "role": "user",
                "content": mongo_query_prompt
            }
        ],
        temperature=0,
        max_tokens=32768,
        )
    
    mongo_query_str = mongo_query_groq.choices[0].message.content
    mongo_query_json = json.loads(mongo_query_str)
    return mongo_query_json
    
def run_mongo_query(collection_name,mongo_query_json):
    pipeline = mongo_query_json
    result = collection_name.aggregate(pipeline)
    result_list = []
    for doc in result:
        result_list.append(doc)
    # result_list
    result_str = str(result_list)
    # result_str
    return result_str

def final_ans_mongo(mongo_schema,result_str, user_question):
    final_answer_prompt = """You are a helpful, nosql database agent, named "Babelfish.db", that talks very nicely and humbly!
    Here is the table schema and description of my nosql mongodb database:
    """ + mongo_schema + """ 
    From the above described nosql mongodb database, the user has asked the following question: """ + user_question + """ 
    The answer to the question is: """ + result_str + """ 
    Tell this result to the user in natural language. Be Polite!"""
    
    final_ans_chat = groq_client.chat.completions.create(
        model="mixtral-8x7b-32768",
        messages=[
            {
                "role": "user",
                "content": final_answer_prompt
            }
        ],
        temperature=0,
        max_tokens=32768,
        )
    final_ans = final_ans_chat.choices[0].message.content
    return final_ans


#report-pdf
class PDF(FPDF):
    def __init__(self,db_name):
        super(PDF, self).__init__()
        self.first_page_header_added = False  # Initialize before adding pages
        self.set_auto_page_break(auto=True, margin=15)
        self.db_name = db_name 
        self.add_page()
        self.set_font('Times', size=13)
    
    def header(self):
        if not self.first_page_header_added:
            self.set_font('Times', 'B', 15)
            self.cell(0, 5, f'{self.db_name} database chat report', ln=True, align='L')
            self.set_font('Times', 'I', 9)
            current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.cell(0, 7, 'Report generated at '+current_datetime, ln=True, align='L')
            self.first_page_header_added = True
            self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Times', 'I', 10)
        self.cell(0, 10, 'Created with Babelfish.db', 0, 0, 'R')

    def write_text(self, text, line_height=8):
        for line in text.splitlines():
            self.multi_cell(0, line_height, line)

def generate_report(conversation):
    conversation_str = str(conversation)
    report_prompt = """I am going to provide you the conversation of a user with a database assistant.
    Create a report of this conversation in a structured like the given example:

    example:
    '''
    User: How many employees are there?
    Assistant: There are 23 employees in the database.

    User: who is the sales executive assigned to Rovelli Gifts?
    Assistant: The sales executive assigned to Rovelli Gifts is John Doe.
    '''
    Just create a report like above for the conversation provided below.

    Conversation:

    """ +  conversation_str + """ 

    Make the report in a chat format, without altering the sequence of the conversation and any data. Do not add any title.
    Also, \\n in the conversation means newline
    **Very Important: Do not manipulate, or add or delete anything to/ from data, Just structure it.
    Add a - in front of new chat
    Add new line after one user and assistant message pair 
    Do not manipulate data."""
    print("generating report...")
    generate_report = groq_client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[
            {
                "role": "user",
                "content": report_prompt
            }
        ],
        temperature=0,
        max_tokens=32768,
    )

    report_text = generate_report.choices[0].message.content
    return report_text

def generate_pdf(db_name, report_text):

    buffer = io.BytesIO()
    pdf = PDF(db_name)
    pdf.write_text(report_text)
    # pdf.output(dest='S').encode('latin1')
    buffer.write(pdf.output(dest='S').encode('latin1',errors='replace'))
    buffer.seek(0)
    
    buffer = io.BytesIO()
    pdf.output(dest='S').encode('latin1')
    buffer.write(pdf.output(dest='S').encode('latin1'))
    buffer.seek(0)
    
    return buffer


st.set_page_config(
    page_title="Babelfish.db",
    page_icon="🐠",
)


st.title("🐠 Babelfish.db")
st.subheader("Talk to your database in natural language 🗣")

st.sidebar.title("Connect your database")
database = st.sidebar.selectbox("Choose the database you want to connect:", ("My SQL", "Mongo DB"))




if database == "My SQL":

    if "db" not in st.session_state:
        st.session_state.db = None
        
    if "sql_schema" not in st.session_state:
        st.session_state.sql_schema = None

    if 'show_success' not in st.session_state:
        st.session_state.show_success = False
    
    if 'show_failure' not in st.session_state:
        st.session_state.show_failure = False

    with st.sidebar.form(key="sidebar_form"):
        db_user = st.text_input("Username:")
        db_password = st.text_input("Password:",type="password")
        db_host = st.text_input("Host ('localhost' for local databases):")
        db_name = st.text_input("Schema Name:")
        submitted = st.form_submit_button("Connect")

    if submitted:
        # global db, sql_schema
        if db_user and db_password and db_host and db_name:
            print("Connecting...")
            try:
                st.session_state.db = connect_mysql(db_user, db_password, db_host, db_name)
                st.session_state.sql_schema = st.session_state.db.get_table_info()


                # print(st.session_state.db)

                print("Connected")
                if st.session_state.db:
                    st.session_state.show_success = True
                    if st.session_state.show_success:
                        st.sidebar.success('Successfully connected to your database: '+db_name)

                else:
                    st.session_state.show_failure = True
                    if st.session_state.show_failure:
                        st.sidebar.error('Failed to connect to your database: '+db_name)

            except ProgrammingError as e:
                print("pro err")
                st.session_state.show_failure = True

                pattern = "Access Denied for user"
                match = re.search(pattern,str(e))

                if match:
                    if st.session_state.show_failure:
                        st.sidebar.error(f'Access Denied for user {db_user}. Please check your credentials.')
                else:
                    if st.session_state.show_failure:
                        st.sidebar.error('Failed to connect to your database: '+db_name)
                        print(e)


            except Exception as e:
                # print(f"Exception type: {type(e).__name__}")
                st.session_state.show_failure = True
                if st.session_state.show_failure:
                    st.sidebar.error('Failed to connect to your database: '+db_name)
                print(e)
        else:
            st.session_state.show_failure = True
            if st.session_state.show_failure:
                st.sidebar.error('Please fill all the fields.')



    if "messages" not in st.session_state:
        st.session_state.messages = []

    if 'report_text' not in st.session_state:
        st.session_state.report_text = None

    if 'pdf_buffer' not in st.session_state:
        st.session_state.pdf_buffer = None

    for message in st.session_state.messages:
        
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("What can I help you with?"):

        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):

            if st.session_state.sql_schema:
                sql_query = generate_sql_query(st.session_state.sql_schema,prompt)
                if sql_query:
                    # print(sql_query)
                    try:
                        sql_ans = run_sql_query(st.session_state.db, sql_query)
                        if sql_ans:
                            final_ans = final_sql_ans(prompt, sql_query, sql_ans)
                            if final_ans:
                                response = st.write(final_ans)
                                st.session_state.messages.append({"role": "assistant", "content": final_ans})
                            else:
                                response = st.write("Sorry, I couldn't understand your question. Please try again!")
                                st.session_state.messages.append({"role": "assistant", "content": "Sorry, I couldn't understand your question. Please try again!"})
                        else:
                            response = st.write("Sorry, I couldn't understand your question. Please try again!")
                            st.session_state.messages.append({"role": "assistant", "content": "Sorry, I couldn't understand your question. Please try again!"})
                    except Exception as e:
                        print(e)
                        response = st.write("Sorry, I couldn't understand your question. Please try again!")
                        st.session_state.messages.append({"role": "assistant", "content": "Sorry, I couldn't understand your question. Please try again!"})
                else:
                    response = st.write("Sorry, I couldn't understand your question. Please try again!")
                    st.session_state.messages.append({"role": "assistant", "content": "Sorry, I couldn't understand your question. Please try again!"})
            else:
                #no db connected
                response = st.write("Database is not connected. Connect you database from the sidebar.")
                st.session_state.messages.append({"role": "assistant", "content": "Database is not connected. Connect you database from the sidebar."})



    if st.button('Generate Report'):
        
        if st.session_state.messages:
            st.session_state.report_text = generate_report(st.session_state.messages)
            st.session_state.pdf_buffer = generate_pdf(db_name,st.session_state.report_text)

            if st.session_state.pdf_buffer is not None:
                st.download_button(
                    label="Download PDF",
                    data=st.session_state.pdf_buffer.getvalue(),
                    file_name= f"{db_name}_chat_report.pdf",
                    mime="application/pdf"
                )
        else:
            st.write("Please start a conversation first!")  
            # st.write("Chat history is empty. Feel free to ask a question and then generate report!")

if database == "Mongo DB":

    if "col_name" not in st.session_state:
        st.session_state.db = None

    if 'show_success' not in st.session_state:
        st.session_state.show_success = False
    
    if 'show_failure' not in st.session_state:
        st.session_state.show_failure = False

    if "mongo_schema" not in st.session_state:
        st.session_state.mongo_schema = None

    if "mongo_example" not in st.session_state:
        st.session_state.mongo_example = None

    with st.sidebar.form(key="sidebar_form"):
        db_user = st.text_input("Username:")
        db_password = st.text_input("Password:",type="password")
        db_host = st.text_input("Host ('localhost' for local databases):")
        db_name = st.text_input("Database Name:")
        collection_name = st.text_input("Collection Name:")
        submitted = st.form_submit_button("Connect")

    if submitted:
        if db_user and db_password and db_host and db_name and collection_name:

            print("Connecting...")
            try:
                st.session_state.col_name = connect_mongodb(db_user,db_password,db_host,db_name, collection_name)
                # st.session_state.show_success = True

                # print(st.session_state.col_name)

                print("Connected")
                if st.session_state.col_name is not None:
                    # print("i am reachable")
                    st.session_state.show_success = True
                    if st.session_state.show_success:
                        st.sidebar.success('Successfully connected to your database: '+db_name)

                else:
                    st.session_state.show_failure = True
                    if st.session_state.show_failure:
                        st.sidebar.error('Failed to connect to your database: '+db_name)


            except OperationFailure as e:
                st.session_state.show_failure = True

                pattern = 'Authentication failed'
                match = re.search(pattern,str(e))

                if match:
                    st.sidebar.error('Authentication failed. Please check your credentials.')
                else:
                    st.sidebar.error(f'Failed to connect to your database: {db_name}')
                    print(e)


            except Exception as e:
                st.session_state.show_failure = True
                if st.session_state.show_failure:
                    st.sidebar.error(f'Failed to connect to your database: {db_name}')
                print(e)
        else:
            st.session_state.show_failure = True
            if st.session_state.show_failure:
                st.sidebar.error('Please fill all the fields.')


    if "mongo_messages" not in st.session_state:
        st.session_state.mongo_messages = []

    if 'report_text_mongo' not in st.session_state:
        st.session_state.report_text_mongo = None

    if 'pdf_buffer_mongo' not in st.session_state:
        st.session_state.pdf_buffer_mongo = None

    for message in st.session_state.mongo_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


    if prompt := st.chat_input("What can I help you with?"):

        st.session_state.mongo_messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)


        with st.chat_message("assistant"):

            mongo_schema = st.session_state.mongo_schema
            mongo_example = st.session_state.mongo_example
            if mongo_schema and mongo_example:
                mongo_query = generate_mongo_query(mongo_schema,mongo_example,prompt)
                if mongo_query:
                    # print(mongo_query)
                    result = run_mongo_query(st.session_state.col_name, mongo_query)
                    if result:
                        final_ans = final_ans_mongo(mongo_schema,result,prompt)
                        if final_ans:
                            ans = st.write(final_ans)
                            st.session_state.mongo_messages.append({"role": "assistant", "content": final_ans})
                        else:
                            ans = st.write("Sorry, I could not understand your question. Please try again!")
                            st.session_state.mongo_messages.append({"role": "assistant", "content": "Sorry, I could not understand your question. Please try again!"})
                    else:
                        ans = st.write("Sorry, I could not understand your question. Please try again!")
                        st.session_state.mongo_messages.append({"role": "assistant", "content": "Sorry, I could not understand your question. Please try again!"})
                else:
                    ans = st.write("Sorry, I could not understand your question. Please try again!")
                    st.session_state.mongo_messages.append({"role": "assistant", "content": "Sorry, I could not understand your question. Please try again!"})
            else:
                #db not connected
                ans = st.write("Database is not connected. Connect you database from the sidebar.")
                st.session_state.mongo_messages.append({"role": "assistant", "content": "Database is not connected. Connect you database from the sidebar."})
                


    if st.button('Generate Report'):

        if st.session_state.mongo_messages:
            # print(st.session_state.mongo_messages)
            st.session_state.report_text = generate_report(st.session_state.mongo_messages)
            st.session_state.pdf_buffer = generate_pdf(db_name,st.session_state.report_text)

            if st.session_state.pdf_buffer is not None:
                st.download_button(
                    label="Download PDF",
                    data=st.session_state.pdf_buffer.getvalue(),
                    file_name= f"{db_name}_chat_report.pdf",
                    mime="application/pdf"
                )
        else:
            st.write("Please start a conversation first!")
            # st.write("Chat history is empty. Feel free to ask a question and then generate report!")


                        





