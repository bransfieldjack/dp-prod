from flask import request, session, Response, Blueprint, send_from_directory, send_file
from functools import lru_cache
from collections import OrderedDict
from jinja2 import TemplateNotFound
import itertools
import re, os
# import boto3
import glob
from flask import Flask, Blueprint, render_template, request, Response, redirect, url_for, jsonify
from flask_cors import CORS # Extension for handling Cross Origin Resource Sharing.
from flask_api import FlaskAPI, status, exceptions  # Flask API allows boiler plate browseable API. 
import psycopg2, json, os, pandas
from psycopg2 import extras
from pathlib import Path    # Similar to os.path - used to load the swagger.json configuration and serve on root path '/'.
from app.api.models import datasets, UserModel, _runSql
from flask_swagger_ui import get_swaggerui_blueprint    # Required for swagger UI templating. 
import pymongo
from pymongo import MongoClient
from pprint import pprint # pprint library is used to make the output look more pretty
import pandas as pd
from pprint import pprint # pprint library is used to make the output look more pretty
import gridfs
from bson.json_util import dumps
from app.api.models import UserModel as user
import flask_login
from app import app


module = Blueprint('s3_storage', __name__)

mongo_uri = app.config["MONGO_URI"]
mongo_uri = app.config["MONGO_URI"]
myclient = pymongo.MongoClient(mongo_uri)
database = myclient["dataportal_prod_meta"]
collection = database["datasets"]
expression_files_storage = app.config["PATHTOEXPRESSIONFILES"]


@module.route("/expression_files", methods=['GET', 'POST'])
def expression_files():

    data = request.get_json()
    token = data['token']
    ds_id = data['dataset_id']
    file_name = '/' + str(ds_id) + '*' + '.tsv'
    expression_file = glob.glob(expression_files_storage + file_name)

    return {
        "path": str(ds_id) + '.tsv'
    }
   
