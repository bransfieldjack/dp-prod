import flask
import os
import jwt
import json
from app.api.models import _runSql
from flask_login import login_user
from app import app
from flask_cors import CORS, cross_origin
from smtplib import SMTP
from flask import Flask, session, Blueprint, render_template, request, Response, redirect, url_for, jsonify
from app.api.models import datasets, UserModel, _runSql
import pymongo
from pymongo import MongoClient
import flask_login
from bson import json_util
from bson.json_util import dumps
from app import app
from datetime import date

"""
The page that this is rendering gets most of its functionality
(get/post requests) from the API, which is why there arent many methods required. 
"""

module = Blueprint('annotation', __name__)
mongo_uri = app.config["MONGO_URI"]
myclient = pymongo.MongoClient(mongo_uri)
database = myclient["dataportal_prod_meta"]
governanceDatabase = myclient["dataportal_prod_governance"]
collection = database["datasets"]
governanceCollection = governanceDatabase["annotator_interactions"]


@module.route('/annotation')
def annotation():
    
    if session["loggedIn"] == True:
        user = session["user"]
        role = session["role"]
        return render_template('/api/annotation.html', user=user, role=role)
    else:
        return redirect('/login_error')


@module.route('/getAnnotator', methods=['GET', 'POST'])
def getAnnotator():
    """
    Checks if a dataset has as assigned annotator, used in handClick() on annotation-base.html.
    """

    data = request.get_json()
    dataset_id = data['dataset_id']
    document = collection.find_one({'dataset_id': dataset_id})

    return {'annotator': document['annotator']}


@module.route('/assignAnnotator', methods=['GET', 'POST'])
@cross_origin()
def assignAnnotator():
    """
    Assigns a user to a dataset for annotation. 
    """
    
    cursor = collection.find({})

    data = request.get_json()
    payload = data['data']
    dataset_id = payload['dataset_id']
    username = payload['username']
    password = payload['password']
    email = username

    _username = UserModel.User(email)
    auth = _username.authenticate(email, password)

    if auth == True:
        document = collection.find_one({'dataset_id': dataset_id})
        if document["annotator"] == "":
            try: 
                myquery = { "dataset_id": dataset_id }
                newvalues = { "$set": { "annotator": email, "can_annotate": True } }
                collection.update_one(myquery, newvalues)

                """
                Below code: future iteration for recording actions with the governance table. 
                """
                # message = username + " " + "added to dataset" + " " + dataset_id
                # today = date.today()
                # governanceCollection.insert({"name" : username, "role" : role, "notes" : message, "date" : today })
                
                return email + " " + "is now annotating this dataset."
                # collection.update({"dataset_id": dataset_id}, {"$set": {"annotator": username, "can_annotate": true}}, upsert=False)
            except:
                return "An exception occurred"
        else:
            return "An annotator is already assigned to this dataset. To request a transfer, please contact the system administrator: admin@stemformatics.org"

    else:
        return "User does not exist"


@module.route('/unAssignAnnotator', methods=['GET', 'POST'])
def unAssignAnnotator():
    """
    Remove an annotator.
    """

    data = request.get_json()
    payload = data['data']
    dataset_id = payload['dataset_id']
    # title = payload['title']
    annotator = payload['username']

    try:
        myquery = { "dataset_id": dataset_id }
        newvalues = { "$set": { "annotator": ''} } 
        collection.update_one(myquery, newvalues)
        return "Annotator removed"
    except:
        return "Error, annotator removal unsuccessful. "

    
@module.route('/transferAnnotator', methods=['GET', 'POST'])
def transferAnnotator():
    """
    Assigns a user to a dataset for annotation. 
    """

    data = request.get_json()
    payload = data['data']
    annotator = payload['annotator']
    dataset_id = payload['dataset_id']

    try:
        myquery = { "dataset_id": dataset_id }
        newvalues = { "$set": { "annotator": annotator} } 
        collection.update_one(myquery, newvalues)
        return "Annotator transferred"
    except:
        return "Error, annotator removal unsuccessful. "


@module.route('/search_mongo', methods=['GET', 'POST'])
def search_mongo():

    data = request.get_json()
    dataset_id = data['dataset_id']
    token = data['token']
    myclient = pymongo.MongoClient(mongo_uri)     
    database = myclient["dataportal_prod_meta"]
    collection = database["datasets"]
    result = collection.find_one({'dataset_id': dataset_id})
    
    del result['_id']

    if not token:
        return jsonify({'message': 'Token is missing!'}), 403

    try: 
        jwt.decode(token, app.config['SECRET_KEY'])
        if result != None:
            return json.dumps(result)
        else:
            return {"Message": "No samples found for dataset_id: " + dataset_id}
    except:
        return jsonify({'Message': 'Missing or invalid token.'}), 403
    
    return "Access Denied"


@module.route('/check_dataset_id', methods=['GET', 'POST'])
def check_dataset_id():
    """
    A simple, reusable check to see if a DatasetID already exists in the database. 
    """
    data = request.get_json()
    dataset_id = data['dataset_id']
    # test = _runSql("select * from samples where dataset_id=%s", (dataset_id))
    # print(test)

    token = data['token']
    myclient = pymongo.MongoClient(mongo_uri)     
    database = myclient["dataportal_prod_meta"]
    collection = database["datasets"]
    result = collection.find_one({'dataset_id': int(dataset_id)})

    if result == None:
        return {"result": "false", "response": "Dataset ID does not exist"}

    if result != None:
        return {"result": "true", "response": "Dataset ID already exists!"}


@module.route("/summary_table_mongo", methods=['GET', 'POST'])
def summary_table_mongo():
    
    myclient = pymongo.MongoClient(mongo_uri)     
    database = myclient["dataportal_prod_meta"]
    collection = database["datasets"]
    result = collection.find()

    dict_list = []
    for item in result:
        obj = {
            "data": item
        }
        dict_list.append(obj)
    dict_list.pop(1)

    if session["loggedIn"] == True:
        return dumps(dict_list)
    else:
        return "Access Denied"


@module.after_request  # Necessary to add the response headers for comms back to the UI. Add only authorized front end applications, example: https://ui-dp.stemformatics.org
def add_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'OPTIONS,GET,PUT,POST,DELETE'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response


