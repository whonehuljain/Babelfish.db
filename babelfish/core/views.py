from django.shortcuts import render, redirect
from django.http import JsonResponse
import json, re
from .forms import SqlConnectForm, MongoConnectForm
from langchain_community.utilities import SQLDatabase
from .helper import SQLDatabaseHelper, MongoDatabaseHelper
from pymongo import MongoClient
import pymysql
import urllib.parse

info = None

# Create your views here.
def home(request):
    form = SqlConnectForm()
    form_mongo = MongoConnectForm()
    return render(request, 'home.html', {'form':form, 'form_mongo':form_mongo})


def clear_all_db_sessions(request):

    # Clear MySQL related sessions
    keys_to_remove = [
        'mysql_uri',
        'info',
        # Add any other MySQL related session keys
    ]
    
    # Clear MongoDB related sessions
    mongo_keys = [
        'mongo_uri',
        'mongo_db_name',
        'mongo_collection',
        'mongo_schema',
        'mongo_example',
        'is_atlas'
    ]
    
    keys_to_remove.extend(mongo_keys)
    
    for key in keys_to_remove:
        request.session.pop(key, None)



def mysql(request):
    if request.method == 'POST':
        context = {}
        form = SqlConnectForm(request.POST)
        if form.is_valid():
            db_user = form.cleaned_data['username']
            db_password = urllib.parse.quote(form.cleaned_data['password'])
            db_host = form.cleaned_data['hostname']
            db_name = form.cleaned_data['schema_name']

            port = 3306
            if ':' in db_host:
                db_host, port = db_host.split(':')
                port = int(port)
            
            try:
               
                mysql_uri = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{port}/{db_name}"

                print(f"Attempting to connect to URI: {mysql_uri}...")
                
                connection = pymysql.connect(
                    host=db_host,
                    port=port,
                    user=db_user,
                    password=form.cleaned_data['password'], 
                    database=db_name,
                    charset="utf8mb4",
                    connect_timeout=10,
                    read_timeout=10,
                    write_timeout=10,
                    cursorclass=pymysql.cursors.DictCursor,
                    ssl={
                        "ssl_mode": "REQUIRED"
                    }
                )
                
               
                connection.close()
                
                clear_all_db_sessions(request)
                
                sql_db = SQLDatabase.from_uri(
                    mysql_uri,
                    engine_args={
                        "pool_timeout": 10,
                        "connect_args": {
                            "connect_timeout": 10,
                            "read_timeout": 10,
                            "write_timeout": 10,
                            "ssl": {
                                "ssl_mode": "REQUIRED"
                            }
                        }
                    }
                )
                
                global info
                info = sql_db.get_table_info()
                
                request.session['mysql_uri'] = mysql_uri
                request.session['connection_type'] = 'mysql'
                context['connection_message'] = "Successfully connected to the database!"
                context['dbConnectionStatus'] = 'true'
                return render(request, 'chat.html', context)
                
            except Exception as e:
                context['error'] = f'Error: {str(e)}'
                return render(request, 'chat.html', context)
        
        context['form'] = form
    else:
        context = {"form": SqlConnectForm()}
    return render(request, 'chat.html', context)



def mongodb(request):
    context = {}
    if request.method == 'POST':
        form_mongo = MongoConnectForm(request.POST)
        if form_mongo.is_valid():
            username = form_mongo.cleaned_data['username']
            password = form_mongo.cleaned_data['password']
            hostname = form_mongo.cleaned_data['hostname']
            db_name = form_mongo.cleaned_data['db_name']
            db_collection = form_mongo.cleaned_data['collection_name']
            
            try:

                clear_all_db_sessions(request)


                is_atlas = any(x in hostname.lower() for x in ['.mongodb.net', 'atlas', 'cluster'])
                
                if is_atlas:
                    if not hostname.startswith('mongodb+srv://'):
                       
                        hostname = re.sub(r'^mongodb(\+srv)?://', '', hostname)
                        mongo_uri = f"mongodb+srv://{username}:{password}@{hostname}"
                        if '?' not in hostname:
                            mongo_uri += "/?retryWrites=true&w=majority"
                else:
                    
                    if not hostname.startswith('mongodb://'):
                       
                        hostname = re.sub(r'^mongodb(\+srv)?://', '', hostname)
                        
                        if ':' not in hostname:
                            hostname += ':27017' 
                        mongo_uri = f"mongodb://{username}:{password}@{hostname}"

                print(f"Attempting connection with URI: {mongo_uri}...")



                client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
                client.server_info()

                mongo_db = client[db_name]
                collection = mongo_db[db_collection]
                # print(collection)


                documents_pointer = collection.find().limit(2)
                documents = [doc for doc in documents_pointer]
                doc_str = str(documents)
                mongo_schema = MongoDatabaseHelper.generate_schema_mongo(doc_str)
                mongo_example = MongoDatabaseHelper.generate_example_mongo(mongo_schema)

                
                request.session['mongo_uri'] = mongo_uri
                request.session['mongo_db_name'] = db_name
                request.session['mongo_collection'] = db_collection
                request.session['mongo_schema'] = mongo_schema
                request.session['mongo_example'] = mongo_example
                request.session['is_atlas'] = is_atlas
                request.session['connection_type'] = 'mongodb'

                # print(mongo_schema)

                context['connection_message'] = "Successfully connected to MongoDB!"
                context['success'] = True

            except Exception as e:
                error_msg = str(e)
                if "invalid hostname" in error_msg.lower():
                    context['error'] = "Invalid hostname format. Please check your connection string."
                elif "authentication failed" in error_msg.lower():
                    context['error'] = "Authentication failed. Please check your username and password."
                elif "operation timed out" in error_msg.lower():
                    context['error'] = "Connection timed out. Please check if the database is accessible."
                else:
                    context['error'] = f'Connection Error: {error_msg}'
                context['success'] = False
                print(f"MongoDB Connection Error: {error_msg}")

        else:
            context['error'] = "Invalid MongoDB credentials. Please try again."

    context['form'] = SqlConnectForm()
    context['form_mongo'] = MongoConnectForm()
    return render(request, 'chat.html', context)


def chat(request):

    if request.method == "GET":
        context = {
            'connection_type': request.session.get('connection_type', '')
        }
        return render(request, 'chat.html', context)

    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_prompt = data.get("prompt", "")

            connection_type = request.session.get('connection_type')
            
            # Check if MySQL or MongoDB connection exists
            mysql_uri = request.session.get('mysql_uri')  
            mongo_uri = request.session.get('mongo_uri')
            mongo_db_name = request.session.get('mongo_db_name')
            collection = request.session.get('mongo_collection')
            mongo_schema = request.session.get('mongo_schema')
            mongo_example = request.session.get('mongo_example')

            if connection_type == 'mysql':
                mysql_uri = request.session.get('mysql_uri')
                if not mysql_uri:
                    return JsonResponse({
                        "reply": "MySQL connection not found. Please reconnect to the database."
                    }, status=400)
                

                sql_db = SQLDatabase.from_uri(
                    mysql_uri,
                    engine_args={
                        "pool_timeout": 10,
                        "connect_args": {
                            "connect_timeout": 10,
                            "read_timeout": 10,
                            "write_timeout": 10,
                            "ssl": {
                                "ssl_mode": "REQUIRED"
                            }
                        }
                    }
                )

                sql_query = SQLDatabaseHelper.generate_sql_query(info, user_prompt)
                try:
                    sql_ans = sql_db.run(sql_query)
                except Exception as e:
                    return JsonResponse({"reply": f"MySQL error: {str(e)}"}, status=500)
                
                final_ans = SQLDatabaseHelper.final_sql_ans(user_prompt, sql_query, sql_ans)
                return JsonResponse({"reply": f"{final_ans}"})
            
            elif connection_type == 'mongodb':
                mongo_uri = request.session.get('mongo_uri')
                if not mongo_uri:
                    return JsonResponse({
                        "reply": "MongoDB connection not found. Please reconnect to the database."
                    }, status=400)
                
                # MongoDB
                try:
                    mongo_query = MongoDatabaseHelper.generate_mongo_query(mongo_schema, mongo_example, user_prompt)
                    client = MongoClient(mongo_uri)
                    mongo_db = client[mongo_db_name]    
                    mongo_collection = mongo_db[collection]
                    mongo_result = MongoDatabaseHelper.run_mongo_query(mongo_collection, mongo_query)
                    mongo_ans = MongoDatabaseHelper.final_ans_mongo(mongo_schema, mongo_result, user_prompt)
                    return JsonResponse({"reply": f"{mongo_ans}"})
                except Exception as e:
                    return JsonResponse({"reply": f"MongoDB error: {str(e)}"}, status=500)
            else:
 
                return JsonResponse({
                    "reply": "No active database connection found. Please ensure you're connected to either MySQL or MongoDB."
                }, status=400)
        except json.JSONDecodeError:
            return JsonResponse({"reply": "Invalid JSON in request body"}, status=400)
        except Exception as e:
            return JsonResponse({"reply": f"Server error: {str(e)}"}, status=500)
    return JsonResponse({"reply": "Only POST requests are allowed"}, status=405)