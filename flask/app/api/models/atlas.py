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


class Atlas(object):

    def __init__(self, project):
        # self.datasetId = int(datasetId)
        self.project = project

    def getSamples(self):   
        """
        Method to return all atlas 
        samples based on specified project. 
        """
        if self.project == 'blood':
                database = myclient["blood_v1"]
                collection = database["samples"]

        if self.project == 'myeloid':
            database = myclient["imac_v1"]
            collection = database["samples"]

        result = collection.find()
        self.getSamples = dumps(result)
        return self.getSamples

    def getDatasets(self):   
        """
        Method to return all atlas 
        samples based on specified project. 
        """

        # Configs: 
        mongo_uri = app.config["MONGO_URI"]
        myclient = pymongo.MongoClient(mongo_uri)

        # if self.datasetId is None:
        if self.project == 'blood':
                database = myclient["blood_v1"]
                collection = database["samples"]

        if self.project == 'myeloid':
            database = myclient["imac_v1"]
            collection = database["samples"]

        # myeloid_database = myclient["imac_v1"]
        # myeloid_collection = myeloid_database["samples"]

        samples_database = myclient["dataportal_prod_meta"]
        samples_collection = samples_database["datasets"]

        items = []
        for item in collection.find():
            del item['_id']

            for title in samples_collection.find({'dataset_id': int(item['dataset_id'])}):
                del title['_id']
                
                res = {
                    "atlas": item,
                    "meta": title
                }

                items.append(res)
        
        self.getDatasets = json.dumps(items)
        return self.getDatasets

            # result = collection.find()
            # self.getSamples = dumps(result)
            # return self.getSamples


# # ----------------------------------------------------------
# # Atlas Samples class
# # ----------------------------------------------------------


# class AtlasSamples(object):

#     def __init__(self, project):
#         self.project = project  # Instance att

#     def getSamples(self):   
#         """
#         Method to return all atlas 
#         samples based on specified project. 
#         """
#         if self.project == 'blood':
#                 database = myclient["blood_v1"]
#                 collection = database["samples"]

#         if self.project == 'myeloid':
#             database = myclient["imac_v1"]
#             collection = database["samples"]

#         result = collection.find()
#         self.getSamples = dumps(result)
#         return self.getSamples