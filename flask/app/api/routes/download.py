from flask import request, Response, Blueprint
from functools import lru_cache

from jinja2 import TemplateNotFound
import itertools
from flask_cors import CORS # Extension for handling Cross Origin Resource Sharing.
from flask_api import FlaskAPI, status, exceptions  # Flask API allows boiler plate browseable API. 
import psycopg2, json, os, pandas
from psycopg2 import extras
from pathlib import Path    # Similar to os.path - used to load the swagger.json configuration and serve on root path '/'.
from app.api.models import datasets
from flask_swagger_ui import get_swaggerui_blueprint    # Required for swagger UI templating. 


module = Blueprint('download', __name__)


@module.route('/download', methods=['GET', 'POST'])
def download():

    data = request.get_json()
    payload = data['data']  # This is the dataset_id - print(data) to explore.
    pathToExpressionFiles = "/mnt/data/portal_data/expression/"
    full_file = pathToExpressionFiles + payload['dataset_id'] + ".raw.tsv"

    file = open(full_file,'r')
    returnfile = file.read()
    file.close()
    return Response(returnfile,
        mimetype="text/tsv",
        headers={"Content-disposition": full_file})


@module.after_request  # Necessary to add the response headers for comms back to the UI. Add only authorized front end applications, example: https://ui-dp.stemformatics.org
def add_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'OPTIONS,GET,PUT,POST,DELETE'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response