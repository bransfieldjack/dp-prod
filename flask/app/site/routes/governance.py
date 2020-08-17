import flask
import os
from smtplib import SMTP
from flask import Flask, session, Blueprint, render_template, request, Response, redirect, url_for, jsonify
from app.api.models import datasets, UserModel, _runSql
import pymongo
from bson.json_util import dumps
from app import app


module = Blueprint('governance', __name__)
mongo_uri = app.config["MONGO_URI"]


@module.route('/governance')
def governance():

    if session["loggedIn"] == True:
        user = session["user"]
        return render_template('/api/governance.html', user=user)
    else:
        return redirect('/login_error')


@module.route("/governance_table_mongo", methods=['GET', 'POST'])
def governance_table_mongo():

    myclient = pymongo.MongoClient(mongo_uri) # Mongon container name is 'mongo'. # local mongodb server.   # Connects to the mongodb daabase and returns everything.   
    database = myclient["dataportal_prod_governance"]
    collection = database["annotator_interactions"]
    result = collection.find()
    return dumps(result)