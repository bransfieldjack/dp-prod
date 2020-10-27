import os, pandas, json
from flask import jsonify
from app import app
import psycopg2
from . import _runSql
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import pymongo
from pymongo import MongoClient
from bson.json_util import dumps

postgres_username = app.config['POSTGRES_USERNAME'] # os.environ["POSTGRES_USERNAME"]
postgres_password = app.config["POSTGRES_PASSWORD"]
postgres_database_name = app.config["POSTGRES_DATABASE_NAME"]
postgres_host = app.config["POSTGRES_HOST"]
postgres_port = app.config["POSTGRES_PORT"]
postgres_uri = app.config["PSQL_URI"]
path_to_expression_files = app.config["PATHTOEXPRESSIONFILES"]
conn = psycopg2.connect(postgres_uri)
cursor = conn.cursor()
mongo_uri = app.config["MONGO_URI"]
myclient = pymongo.MongoClient(mongo_uri)


"""
Atlas classes, one for datasets, the other for samples. 
Provide an atlas project name and return data based on that. 
"""

# ----------------------------------------------------------
# Atlas Dataset class
# ----------------------------------------------------------


class AtlasDataset(object):

    def __init__(self, datasetId, project):
        self.datasetId = int(datasetId)
        self.project = project


# ----------------------------------------------------------
# Atlas Samples class
# ----------------------------------------------------------


class AtlasSamples(object):

    def __init__(self, project):
        self.project = project  # Instance att

    def getSamples(self):   

        if self.project == 'blood':
                database = myclient["blood_v1"]
                collection = database["samples"]

        if self.project == 'myeloid':
            database = myclient["imac_v1"]
            collection = database["samples"]

        result = collection.find()
        self.getSamples = dumps(result)
        return self.getSamples