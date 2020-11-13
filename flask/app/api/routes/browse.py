from flask import request, session, Response, Blueprint, send_from_directory
from functools import lru_cache
from collections import OrderedDict
from jinja2 import TemplateNotFound
import itertools
from app.api.models import atlas
import re, os
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


module = Blueprint('browse', __name__)

mongo_uri = app.config["MONGO_URI"]
mongo_uri = app.config["MONGO_URI"]
myclient = pymongo.MongoClient(mongo_uri)
database = myclient["dataportal_prod_meta"]
collection = database["datasets"]


@module.route("/summary_table", methods=['GET', 'POST'])
@lru_cache(maxsize=32)  # Caches the returned value of this function so we dont have to keep re-calling it. 
def summary_table():
    datasetId = 1000
    ds = datasets.Dataset(datasetId)
    summaryTable = ds.summaryTable()
    dataset_id = summaryTable['dataset_id'].to_list()
    title = summaryTable['title'].to_list()
    authors = summaryTable['authors'].to_list()
    description = summaryTable['description'].to_list()
    generic_sample_type = summaryTable['generic_sample_type'].to_list()
    handle = summaryTable['handle'].to_list()

    date_list = []
    for item in handle:
        if item is not None:
            result = item.split("_")
            value = result[1]
            date_list.append(value)
    pubmed = summaryTable['pubmed'].to_list()

    obj_list = []
    for (a, b, c, d, e, f, g) in zip(dataset_id, title, authors, description, generic_sample_type, date_list, pubmed):
        obj = {
            "Dataset_id": a,
            "Title": b,
            "Authors": c,
            "Description": d,
            "generic_sample_type": e,
            "date": f,
            "pubmed": g
        }
        obj_list.append(obj)
    obj_list.pop(0) # The first dict/item in the array is always null - remov. 

    response_object = {
        "count": 10,
        "entries": obj_list
    }

    if session["loggedIn"] == True:
        return response_object
    else:
        return "Access Denied"


@module.route("/summary_table_search", methods=['GET', 'POST'])
def summary_table_search():
    data = request.get_json()
    payload = data['data']
    searchTerm = payload['searchTerm']
    datasetId = 1000
    ds = datasets.Dataset(datasetId)
    summaryTableSearch = ds.summaryTableSearch(str(searchTerm))
    return summaryTableSearch.to_json(orient="split")


@module.route("/samples_update", methods=['GET', 'POST'])
def samples_update():
    data = request.get_json()
    payload = data['data']
    datasetId = payload['dataset_id']
    column = payload['column']
    rowIds = payload['rowIds']
    value = payload['value']
    ds = datasets.Dataset(datasetId)
    updateSampleValue = ds.updateSampleValue(column, rowIds, value)
    return updateSampleValue


@module.route("/atlas_clone_update", methods=['GET', 'POST'])
def atlas_clone_update():
    data = request.get_json()
    payload = data['data']
    column = payload['column']
    rowIds = payload['rowIds']
    value = payload['value']

    dataset_id = data['dataset_id']
    annotator = data['annotator']
    date = data['date']
    project = data['project']

    _atlas = atlas.Atlas(project, dataset_id, annotator)
    updateClone = _atlas.updateClone(date, column, rowIds, value)

    return "test"


@module.route("/atlas_update", methods=['GET', 'POST'])
def atlas_update():
    data = request.get_json()
    payload = data['data']
    datasetId = payload['dataset_id']
    column = payload['column']
    rowIds = payload['rowIds']
    value = payload['value']
    ds = datasets.Dataset(datasetId)
    updateAtlasValue = ds.updateAtlasValue(column, rowIds, value)
    return updateAtlasValue


@module.route("/export_samples_table", methods=['GET', 'POST'])
def export_samples_table():

    """
    Downloads all samples.
    """

    postgres_uri = os.environ["PSQL_URI"]
    conn = psycopg2.connect(postgres_uri)
    data = pd.read_sql("select * from samples_merged;", conn)
    csv_data = data.to_csv()

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition":
                 "attachment; filename=samples.csv"})


@module.route("/get_all_users", methods=['GET', 'POST'])
def get_all_users():
    _user = user.User("jarnyc@unimelb.edu.au")
    get_users = _user.userTable()
    df = get_users.reset_index()
    newdf = df.drop(['password'], axis=1)
    _dict = newdf.to_dict("records")

    return {"users": _dict}


@module.route("/get_assigned_datasets", methods=['GET', 'POST'])
def get_assigned_datasets():

    # cursor = collection.find({})
    cursor = collection.find({'annotator': {'$exists': 'true', "$ne" : ""}})    # Look for all the fields that arent blank. 
    _dict_list = []
    for item in cursor:

        _id = item['_id']
        dataset_id = item['dataset_id']
        annotator = item['annotator']
        title = item['dataset_metadata'][0]['title']

        _dict = {
            '_id': dumps(_id),
            'dataset_id': dataset_id,
            'annotator': annotator,
            'title': title
        }
        _dict_list.append(_dict)

    return {'assigned_datasets': _dict_list}


@module.route("/get_atlas_data", methods=['GET', 'POST'])
def get_atlas_data():
    """
    Return all atlas production data
    """
    data = request.get_json()
    project = data['project']
    _atlas = atlas.Atlas(project)
    datasets = _atlas.getDatasets()
    return datasets
    

@module.route("/atlasAssignAnnotator", methods=['GET', 'POST'])
def atlasAssignAnnotator():

    data = request.get_json()

    columns = data['columns']
    rows = data['rows']

    annotator = data['annotator']
    username = annotator['user']
    password = data['password']
    date = data['date']
    dataset_id = data['dataset_id']
    project = data['project']

    _username = UserModel.User(username)
    auth = _username.authenticate(username, password)
    role = _username.role(username)

    if auth == True:
        if role == 'admin' or role == 'annotator':
            _atlas = atlas.Atlas(project, dataset_id, annotator)
            assignAnnotator = _atlas.assignAnnotator()
            clone = _atlas.cloneDataset(columns, rows, date)
            return clone
    else:
        return "Error in assignment and clone operation"


@module.route('/atlas_get_jobs', methods=['GET', 'POST'])
def atlas_get_jobs():
    """
    Returns all atlas datasets assigned to annotators.
    """
    data = request.get_json()
    project = 'myeloid' # init value for class, but doesnt matter for this functions return value - it will return for all projects. 
    _atlas = atlas.Atlas(project)
    getAllAssigned = _atlas.getAllAssigned()
    
    return getAllAssigned


@module.route('/atlas_get_clone', methods=['GET', 'POST'])
def atlas_get_clone():
    """
    Returns a single clone. 
    """
    data = request.get_json()
    date = data['date']
    project = data['project']
    dataset_id = data['dataset_id']
    annotator = data['annotator']
    _atlas = atlas.Atlas(project, dataset_id, annotator)
    getSingleClone = _atlas.getSingleClone(date)
    return getSingleClone


@module.route('/atlas_remove_job', methods=['GET', 'POST'])
def atlas_remove_job():
    """
    Remove assigned atlas job (admin permissions only).
    """
    data = request.get_json()
    dataset_id = data['dataset_id']
    date = data['date']
    annotator = data['annotator']
    project = data['project']
    _atlas = atlas.Atlas(project, dataset_id, annotator)
    removeJob = _atlas.removeJob(date)
    return removeJob


@module.route("/get_all_myeloid_atlas", methods=['GET', 'POST'])
def get_all_myeloid_atlas():
    """
    Get all datasets in the atlas, return the atlas data for 
    the dataset but also the sample annotation information as well from the dataportal_prod_meta/datasets table.
    """
    data = request.get_json()
    token = data['token']
    
    # Configs: 
    mongo_uri = app.config["MONGO_URI"]
    myclient = pymongo.MongoClient(mongo_uri)

    myeloid_database = myclient["imac_v1"]
    myeloid_collection = myeloid_database["samples"]
    samples_database = myclient["dataportal_prod_meta"]
    samples_collection = samples_database["datasets"]

    myeloid_items = []
    for myeloid_item in myeloid_collection.find():
        del myeloid_item['_id']

        for title in samples_collection.find({'dataset_id': int(myeloid_item['dataset_id'])}):
            del title['_id']
            
            res = {
                "atlas": myeloid_item,
                "meta": title
            }

            myeloid_items.append(res)
         
    return json.dumps(myeloid_items)


@module.route("/get_single_atlas_dataset", methods=['GET', 'POST'])
def get_single_atlas_dataset():
    """
    Get a single dataset in the atlas.
    """
    data = request.get_json()
    dataset_id = data['dataset_id']
    token = data['token']
    project = data['project']
    _atlas = atlas.Atlas(project, dataset_id)
    dataset = _atlas.getSingleDataset()
    return dataset

    



# @module.route("/get_all_myeloid_atlas", methods=['GET', 'POST'])
# def get_all_myeloid_atlas():

#     data = request.get_json()
#     token = data['token']

#     mongo_uri = app.config["MONGO_URI"]
#     myclient = pymongo.MongoClient(mongo_uri)
#     database = myclient["imac_v1"]
#     collection = database["samples"]
#     cursor = collection.find()

#     _dict_list = []
#     for item in cursor:
#         del item['_id']
#         _dict_list.append(item)
    
#     return {"data": _dict_list}


@module.route("/get_all_blood_atlas", methods=['GET', 'POST'])
def get_all_blood_atlas():
    """
    Get all datasets in the atlas, return the atlas data for 
    the dataset but also the sample annotation information as well from the dataportal_prod_meta/datasets table.
    """
    data = request.get_json()
    token = data['token']
    
    # Configs: 
    mongo_uri = app.config["MONGO_URI"]
    myclient = pymongo.MongoClient(mongo_uri)

    blood_database = myclient["blood_v1"]
    blood_collection = blood_database["samples"]
    samples_database = myclient["dataportal_prod_meta"]
    samples_collection = samples_database["datasets"]

    blood_items = []
    for blood_item in blood_collection.find():
        del blood_item['_id']

        for title in samples_collection.find({'dataset_id': int(blood_item['dataset_id'])}):
            del title['_id']
            
            res = {
                "atlas": blood_item,
                "meta": title
            }

            blood_items.append(res)
         
    return json.dumps(blood_items)


@module.route("/get_single_blood_atlas", methods=['GET', 'POST'])
def get_single_blood_atlas():
    """
    Get a single dataset in the atlas.
    """
    data = request.get_json()
    dataset_id = data['dataset_id']
    token = data['token']
    
    # Configs: 
    mongo_uri = app.config["MONGO_URI"]
    myclient = pymongo.MongoClient(mongo_uri)

    blood_database = myclient["blood_v1"]
    blood_collection = blood_database["samples"]
    samples_database = myclient["dataportal_prod_meta"]
    samples_collection = samples_database["datasets"]

    pre_blood_item = blood_collection.find_one({'dataset_id': str(dataset_id)})
    del pre_blood_item['_id']
    blood_item = pre_blood_item

    blood_items = []
    for title in samples_collection.find({'dataset_id': dataset_id}):
        del title['_id']
        
        res = {
            "atlas": blood_item,
            "meta": title
        }

        blood_items.append(res)
         
    return json.dumps(blood_items)

    
@module.after_request  # Necessary to add the response headers for comms back to the UI. Add only authorized front end applications, example: https://ui-dp.stemformatics.org
def add_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'OPTIONS,GET,PUT,POST,DELETE'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

    