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


@module.route('/new_qc_job', methods=['GET', 'POST'])
def new_qc_job():
    """
    Handles saving new qc jobs to the qc collection in mongo.
    """

    mongo_uri = app.config["MONGO_URI"]
    myclient = pymongo.MongoClient(mongo_uri) 
    database = myclient["qc"]
    collection = database["jobs"]
    received = request.get_json()
    insertjob = collection.insert_one(received)

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