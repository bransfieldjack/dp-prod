from flask import request, Response, Blueprint
from functools import lru_cache
import os, json, pandas as pd
from jinja2 import TemplateNotFound
import itertools
from flask_cors import CORS # Extension for handling Cross Origin Resource Sharing.
from flask_api import FlaskAPI, status, exceptions  # Flask API allows boiler plate browseable API. 
import psycopg2, json, os, pandas
from psycopg2 import extras
from pathlib import Path    # Similar to os.path - used to load the swagger.json configuration and serve on root path '/'.
from app.api.models import datasets, UserModel, _runSql
from flask_swagger_ui import get_swaggerui_blueprint    # Required for swagger UI templating. 
from werkzeug import secure_filename
import re
import pymongo
from app import app


module = Blueprint('upload', __name__)


def _runSql(sql, data=None, type="select", printSql=False):
    """Run sql statement.

    Example:
    > result = _runSql("select * from users where email=%s", (email,))
    > [('jarnyc@unimelb.edu.au', 'dofdlfjlejjce', 'admin')]

    data should be a tuple, even if one element.
    type should be one of {"select","update"}

    Returns a list of tuples corresponding to the columns of the selection if type=="select".
    If type=="update", returns the number of rows affected by the update.

    If printSql is True, then the actual sql being executed will be printed
    """
    postgres_username = app.config['POSTGRES_USERNAME'] 
    postgres_password = app.config["POSTGRES_PASSWORD"]
    postgres_database_name = app.config["POSTGRES_DATABASE_NAME"]
    postgres_host = app.config["POSTGRES_HOST"]
    postgres_port = app.config["POSTGRES_PORT"]
    postgres_uri = app.config["PSQL_URI"]
    conn = psycopg2.connect(postgres_uri)
    cursor = conn.cursor()
    mongo_uri = app.config["MONGO_URI"]

    if printSql:  # To see the actual sql executed, use mogrify:
        print(cursor.mogrify(sql, data))
        
    cursor.execute(sql, data)

    if type=="select":
        result = cursor.fetchall()
    elif type=="update":
        result = cursor.rowcount
        conn.commit()  # doesn't update the database permanently without this

    cursor.close()
    conn.close()
    return result


@module.route('/add_dataset_samples', methods=['GET', 'POST'])
def add_dataset_samples():
    """
    Handles formatting submitted samples data into json. 
    """
    _file = request.files['file']
    data = pd.read_csv(_file, sep='\t', header=0)
    dataframe = pd.DataFrame(data)
    data_json = dataframe.to_dict('index')

    existing_table_columns = _runSql("SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'samples';")
    existing_table_columns_flat = [i[0] for i in existing_table_columns]
   
    columns = []

    for col in data.columns:
        columns.append(col)

    columnCheck = all(item in existing_table_columns_flat for item in columns)

    print("Column check status: ")
    print(columnCheck)

    if columnCheck is False:
        return {
            "status": "error",
            "message": "Column spelling/format is incorrect. The API accepts the following column names and format: {} ".format(existing_table_columns_flat),
            "columns": existing_table_columns_flat, 
            "data": data_json
        }

    else :
        return {"columns": existing_table_columns_flat, "data": data_json}


@module.route('/save_dataset', methods=['GET', 'POST'])
def save_dataset():
    """
    Handles saving new samples files, metadata and governance. 
    """

    postgres_username = app.config['POSTGRES_USERNAME'] 
    postgres_password = app.config["POSTGRES_PASSWORD"]
    postgres_database_name = app.config["POSTGRES_DATABASE_NAME"]
    postgres_host = app.config["POSTGRES_HOST"]
    postgres_port = app.config["POSTGRES_PORT"]
    postgres_uri = app.config["PSQL_URI"]
    conn = psycopg2.connect(postgres_uri)
    cursor = conn.cursor()
    mongo_uri = app.config["MONGO_URI"]

    received = request.get_json()
    
    data = received['data']
    annotator_data = data['annotator']
    dataset_metadata_data = data['dataset']
    samples_data = data['samples']
    datasetId = int(dataset_metadata_data['dataset_id'])

    existing_table_columns = _runSql("SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'samples';")
    existing_table_columns_flat = [i[0] for i in existing_table_columns]
    dict_submitted_columns = samples_data['headers']
    submitted_columns = [d['headerName'] for d in dict_submitted_columns]
    rows = samples_data['samples']  # A list of dictionaries. Keys are psql columns, values are psql values. 
    
    for item in rows: 
        item.update({"dataset_id":datasetId})

    columnCheck =  all(item in existing_table_columns_flat for item in submitted_columns)
    dataset_idCheck = cursor.execute("select dataset_id from samples where dataset_id=%s;", (datasetId,))
    result = cursor.fetchone() is not None  # This is a boolean value which determines if the dataset_id is already in the samples table. 

    """
    This block of code handles uploading samples from a submitted text file to the samples table. 
    """
    if columnCheck is True:   # Checks that the format of the data columns being uploaded match the format in the table. 
        
        if result == True:
            cursor.close()
            conn.close()
            return {
                "status": "error",
                "message": "This dataset already exists in the Dataportal."
            }

        if result == False:
            """
            ============================================================================================================================
            This block handles adding the annotator governance data to mongodb.
            The name of the database in mongo is "dataportal_prod_governance" and the name of the collection is "annotator_interactions".
            ============================================================================================================================
            """
            myclient = pymongo.MongoClient(mongo_uri) # Mongo container name is 'mongo'. # local mongodb server.   # Connects to the mongodb daabase and returns everything.
            database = myclient["dataportal_prod_governance"]
            collection = database["annotator_interactions"]
            annotator_data_write = collection.insert_one(annotator_data)

            """
            ===========================================================================================
            This block handles adding dataset metadata to the dataportal_prod_meta database in mongodb.
            ===========================================================================================
            """
            mongo_uri = app.config["MONGO_URI"]
            myclient = pymongo.MongoClient(mongo_uri) # Mongo container name is 'mongo'. # local mongodb server.   # Connects to the mongodb daabase and returns everything.
            database = myclient["dataportal_prod_meta"]
            collection = database["datasets"]

            dataset_id_dict = int(dataset_metadata_data['dataset_id'])
            title_dict = dataset_metadata_data['title']
            authors_dict = dataset_metadata_data['authors']
            platform_dict = dataset_metadata_data['platform']
            pubmed_dict = dataset_metadata_data['pubmed']
            description_dict = dataset_metadata_data['description']

            value_dict = {
                "dataset_id": dataset_id_dict,
                "datasets": [
                    {
                        "id": dataset_id_dict,
                        "lab": "",
                        "dtg": "",
                        "handle": "", 
                        "published" : "", 
                        "private" : "", 
                        "chip_type" : "", 
                        "min_y_axis" : "", 
                        "show_yugene" : "", 
                        "show_limited" : "",
                        "db_id" : "", 
                        "number_of_samples" : "", 
                        "data_type_id" : "", 
                        "mapping_id" : "", 
                        "log_2" : ""
                    }
                ],
                "dataset_metadata": [
                    {
                        "dataset_id": dataset_id_dict,
                        "title": title_dict,
                        "authors": authors_dict,
                        "description": description_dict,
                        "pubmed": pubmed_dict,
                        "contact_name": "",
                        "contact_email": "",
                        "release_date": "",
                        "platform": ""
                    }
                ]
            }
                
            dataset_metadata_data_write = collection.insert_one(value_dict)
       
            """
            ========================================
            This block handles updating the samples.
            ========================================
            """
            columns = rows[0].keys()
            query = "INSERT INTO samples ({}) VALUES %s".format(','.join(columns))

            values = [[value for value in row.values()] for row in rows]
            
            psycopg2.extras.execute_values(cursor, query, values)
            updated_records = cursor.rowcount
            conn.commit()
            cursor.close()
            conn.close()

            return {
                "status": "success",
                "message": "Upload has completed without errors.",
                "updated_records": updated_records
            }

    else:
        return {
            "status": "error",
            "message": "Column spelling/format is incorrect. The API accepts the following column names and format: {} ".format(existing_table_columns_flat)
        }

        
