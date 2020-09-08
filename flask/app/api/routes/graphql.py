from ariadne import QueryType, ObjectType, graphql_sync, make_executable_schema
from ariadne.constants import PLAYGROUND_HTML
from flask import Flask, request, jsonify, Response, Blueprint
from flask_cors import CORS, cross_origin
from bson import json_util
from app import app
import pymongo
import json


module = Blueprint('graphql', __name__)


# #Support doc: https://ariadnegraphql.org/docs/intro
# # The gql utility function helps catch errors in your gql setup - use it!

# Schema here:
# The query type defines the queries that can be sent to the API.
# Underneath are the queries. 



type_defs = """
    scalar JSON 
    type Query {
        hello: String!
        user: User
        datasets: JSON!
    }

    type User {
        username: String!
    }
"""


query = ObjectType("Query")
user = ObjectType("User")


@query.field("user")
def resolve_username(obj, *_):
    request = info.context
    user_agent = request.headers.get("User-Agent", "Guest")
    # print(request.headers)
    return user_agent


@query.field("datasets")
# @cross_origin(origin='*',headers=['Content-Type','Authorization'])
def resolve_datasets(_, info):

    mongo_uri = app.config["MONGO_URI"]
    myclient = pymongo.MongoClient(mongo_uri)
    database = myclient["dataportal_prod_meta"]
    collection = database["datasets"]
    cursor = collection.find()

    # print(cursor[3])

    # print(cursor[3]["dataset_id"])
    
    
    dict_list = []
    for item in cursor:    

        del item["_id"] # Drop the object ID or the json encoding will contain slashes. 
        conv = json.dumps(item, default=json_util.default)
        dict_list.append(item)

    return dict_list


@query.field("hello")
def resolve_hello(_, info):
    request = info.context
    user_agent = request.headers.get("User-Agent", "Guest")
    # print(request.headers)
    return "testing"


@module.route("/graphql", methods=["GET"])
def graphql_playground():
    # On GET request serve GraphQL Playground
    # You don't need to provide Playground if you don't want to
    # but keep on mind this will not prohibit clients from
    # exploring your API using desktop GraphQL Playground app.
    return PLAYGROUND_HTML, 200


@module.route("/graphql", methods=["POST"])
def graphql_server():
    # GraphQL queries are always sent as POST
    data = request.get_json()

    # Note: Passing the request to the context is optional.
    # In Flask, the current request is always accessible as flask.request
    success, result = graphql_sync(
        schema,
        data,
        context_value=request,
        debug=app.debug
    )

    status_code = 200 if success else 400
    return jsonify(result), status_code

schema = make_executable_schema(type_defs, query, user)