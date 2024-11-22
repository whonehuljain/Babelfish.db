import os
from dotenv import load_dotenv
# from fpdf import FPDF
import io
# from datetime import datetime
# from pymongo import MongoClient
# from pymongo.errors import OperationFailure
# from mysql.connector import ProgrammingError
import json
from groq import Groq
from langchain_community.agents import *
# from langchain_community.utilities import SQLDatabase
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

load_dotenv()

output_parser = StrOutputParser()
groq_api_key = os.environ.get("GROQ_API_KEY")
llm = ChatGroq(model="llama-3.1-70b-versatile",api_key=groq_api_key)
groq_client = Groq(api_key=groq_api_key)



class SQLDatabaseHelper:

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

    def final_sql_ans(user_question, sql_query, sql_ans):
        template = """You are a helpful mysql database agent, named "Babelfish.db"!
        Based on the question, sql query, and sql response, write a natural language response:
        
        Question: {question}
        Sql query: {query}
        SQL Response: {response}

        Tell this result to the user in natural language. Just provide the answer untill not asked for the query! 
        If the question mentions that they wanna know the query, then only return the query.
        Keep the response small and to the point"""

        prompt_response = ChatPromptTemplate.from_template(template)

        full_chain = prompt_response | llm | output_parser

        final_ans = full_chain.invoke({"question":user_question,"query":sql_query,"response":sql_ans})
        return final_ans
    
    

    
class  MongoDatabaseHelper:
    
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
        final_answer_prompt = """You are a helpful, nosql mongodb database agent, named "Babelfish.db"!
        Here is the table schema and description of my nosql mongodb database:
        """ + mongo_schema + """ 
        From the above described nosql mongodb database, the user has asked the following question: """ + user_question + """ 
        The answer to the question is: """ + result_str + """ 
        Tell this result to the user in natural language. Just provide the answer untill not asked for the query! 
        Keep the response small and to the point"""
        
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