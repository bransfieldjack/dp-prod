import flask
import os, pandas as pd
import json
from smtplib import SMTP
from flask import Flask, session, Blueprint, render_template, request, Response, redirect, url_for, jsonify
from app.api.models import datasets, UserModel, _runSql
import pymongo
from pymongo import MongoClient
import flask_login
from bson.json_util import dumps
from app import app


"""
Renders the atlas page.  
"""

module = Blueprint('atlas', __name__)
mongo_uri = app.config["MONGO_URI"]


@module.route('/atlas')
def atlas():
    
    if session["loggedIn"] == True:
        user = session["user"]
        return render_template('/api/atlas.html', user=user)
    else:
        return redirect('/login_error')


@module.route("/atlas_summary_table_mongo", methods=['GET', 'POST'])
def atlas_summary_table_mongo():

    data = request.get_json()
    payload = data['data']
    blood = payload.get("blood", "default_value")
    iMAC = payload.get("iMAC", "default_value")

    myclient = pymongo.MongoClient(mongo_uri) # Mongon container name is 'mongo'. # local mongodb server.   # Connects to the mongodb daabase and returns everything.
    database = myclient["dataportal_prod_meta"]
    collection = database["datasets"]

    if blood == False and iMAC == False:
        result = _runSql("select distinct(dataset_id) from atlas;".format(blood, iMAC))

        flat_result = list(sum(result, ())) # A flat list of all the atlas dataset ids.

        data = []

        for item in flat_result:

            mongo_result = collection.find({"dataset_id": item})

            for item in mongo_result:
                obj = {
                    "data": item
                }
                data.append(obj)

        return dumps(data)

    else:
        result = _runSql("select distinct(dataset_id) from atlas where include_blood={} and include_imac={};".format(blood, iMAC))
        
        flat_result = list(sum(result, ())) # A flat list of all the atlas dataset ids.

        data = []

        for item in flat_result:

            mongo_result = collection.find({"dataset_id": item})

            for item in mongo_result:
                obj = {
                    "data": item
                }
                data.append(obj)

        return dumps(data)


@module.route("/atlas_samples_summary_table_mongo", methods=['GET', 'POST'])
def atlas_samples_summary_table_mongo():

    rows = _runSql("select * from atlas;")
    columns = _runSql("SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'atlas';") 
    flat_columns = list(sum(columns, ()))
    df = pd.DataFrame(rows, columns=flat_columns)
    # newdf = df[['dataset_id', 'sample_id', 'annotator', 'evidence', 'blood_tier1', 'blood_tier2', 'blood_tier3', 'imac_tier1', 'imac_tier2', 'imac_tier3', 'phenotype', 'activation_status', 'display_metadata']]
    # print(df)
    jsonSampleTable = df.to_json(orient="split")

    if session["loggedIn"] == True:
        return jsonSampleTable
    else:
        return "Access Denied"


