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


module = Blueprint('qc', __name__)
mongo_uri = app.config["MONGO_URI"]


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


@module.route('/new_qc_job', methods=['GET', 'POST'])
def new_qc_job():
    """
    Handles saving new qc jobs to the qc collection in mongo.
    """

    # insert_postgres = _runSql("select * from samples")
    # print(insert_postgres)
    
    mongo_uri = app.config["MONGO_URI"]
    myclient = pymongo.MongoClient(mongo_uri) 
    database = myclient["qc"]
    collection = database["jobs"]
    received = request.get_json()
    insertjob = collection.insert_one(received)

    metaDatabase = myclient["dataportal_prod_meta"]
    metaCollection = metaDatabase["datasets"]

    insertMeta = metaCollection.insert_one({ "dataset_id": received['ds_id'],
        "title":" ",
        "authors":" ",
        "description":" ",
        "platform":" ",
        "number_of_samples":" ",
        "private":" ",
        "pubmed_id":" ",
        "annotator":" ",
        "can_annotate":" ",
        "name":" ",
        "accession":" ",
        "sample_types":[ ]
    })

    return {
        "status": "success",
        "message": "Upload has completed without errors.",
    }


@module.route('/jobs_status', methods=['GET', 'POST'])
def jobs_status():
    """
    Returns the status of QC jobs, processing or processed. 
    """

    mongo_uri = app.config["MONGO_URI"]
    myclient = pymongo.MongoClient(mongo_uri) 
    database = myclient["qc"]
    collection = database["jobs"]

    processing_list = []
    processing = collection.find({'job_status': 'incomplete'})

    for item in processing:
        processing_list.append(item["job_status"] == 'incomplete')

    processed_list = []
    processed = collection.find({'job_status': 'complete'})

    for item in processed:
        processed_list.append(item["job_status"] == 'complete')

    count_processing = len(processing_list)
    count_processed = len(processed_list)

    return {
        "processing": count_processing,
        "processed": count_processed
    }


@module.route('/get_jobs', methods=['GET', 'POST'])
def get_jobs():
    """
    Returns all qc jobs. 
    """
    data = request.get_json()
    token = data['token']
    myclient = pymongo.MongoClient(mongo_uri)     
    database = myclient["qc"]
    collection = database["jobs"]
    result = collection.find()

    jobs_list = []
    for item in result:
        del item['_id']
        jobs_list.append(item)

    return {
        "data": jobs_list
    }