from flask import Flask, jsonify, render_template, url_for
from flask_login import LoginManager
from flask_restplus import Api, Resource, fields
from werkzeug.contrib.fixers import ProxyFix
from dotenv import load_dotenv
import os
from os import environ
from flask_cors import CORS, cross_origin


app = Flask(__name__)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})
app.wsgi_app = ProxyFix(app.wsgi_app)
app.config['SECRET_KEY'] = 'st3mf0rmatics2010'
# login = LoginManager(app)
cors = CORS(app, resources={r"/*": {"origins": "*"}})
app.config['CORS_HEADERS'] = 'Content-Type'
# load dotenv in the base root
APP_ROOT = os.path.join(os.path.dirname(__file__), '..')   # refers to application_top/or app root. 
dotenv_path = os.path.join(APP_ROOT, '.env')
load_dotenv(dotenv_path)
app.config.from_envvar('APP_SETTINGS')

authorizations = {  # This dictionary tells flask_rest_plus to expect a token.
    'apikey': {
        'type': 'apiKey',   # Type of token will be an apikey. 
        'in': 'header', # The location where I'm expecting the key, the header.
        'name': 'X-API-KEY'
    }
} 


api_app = Api(app = app, authorizations=authorizations, version = "1.0", 
		  title = "Stemformatics API", 
		  description = "The Stemformatics API facilitates access to all of our public datasets. \n\n Maintainer: jack.bransfield@unimelb.edu.au \n\n [Dataportal Login](https://api.stemformatics.org/dataportal) \n\n [Get JWT Token](https://api.stemformatics.org/jwt_token)")

lookup_dataset_name_space = api_app.namespace('lookup', description='Check a datasets status (public/private)')

public_dataset_name_space = api_app.namespace('samples / metadata', description='Data-types: samples, metadata ')
public_dataset_expression_name_space = api_app.namespace('expression', description='Data-types: expression ')

private_dataset_name_space = api_app.namespace('(private) samples / metadata', description='Data-types: samples, metadata ')
private_dataset_expression_name_space = api_app.namespace('(private) expression', description='Data-types: expression ')


########################################################################################################################################################################
# Prod swagger config (https)
# @property
# def specs_url(self):
#     """Monkey patch for HTTPS - this is to get swagger ui docs working with both http & https. Dev server might be http while prod https for example. """
#     return url_for(self.endpoint('specs'), _external=True, _scheme='https')
########################################################################################################################################################################


########################################################################################################################################################################
# Dev swagger config (http)
@property
def specs_url(self):
    """Monkey patch for HTTPS - this is to get swagger ui docs working with both http & https. Dev server might be http while prod https for example. """
    return url_for(self.endpoint('specs'), _external=True, _scheme='http')
########################################################################################################################################################################

Api.specs_url = specs_url

from app.api.routes.graphql import module
from app.api.routes.browse import module
from app.api.routes.download import module
from app.api.routes.dataset import module
from app.api.routes.upload import module
from app.api.routes.qc import module

from app.site.routes.api_login import module
from app.site.routes.admin import module
from app.site.routes.annotation import module
from app.site.routes.atlas import module
from app.site.routes.home import module
from app.site.routes.governance import module
from app.site.routes.dataset_search import module
from app.site.routes.dataset_upload import module
from flask_swagger_ui import get_swaggerui_blueprint    # Required for swagger UI templating. 

# API Routes:
app.register_blueprint(api.routes.graphql.module, url_prefix='/api')
app.register_blueprint(api.routes.browse.module, url_prefix='/api')
app.register_blueprint(api.routes.dataset.module, url_prefix='/api')
app.register_blueprint(api.routes.download.module, url_prefix='/api')
app.register_blueprint(api.routes.upload.module, url_prefix='/api')
app.register_blueprint(api.routes.qc.module, url_prefix='/api')

# Site routes:  (Sites is just a place where you can store either templates or swagger/UI documentation.)
app.register_blueprint(site.routes.api_login.module, url_prefix='/')
app.register_blueprint(site.routes.admin.module, url_prefix='/')
app.register_blueprint(site.routes.annotation.module, url_prefix='/')
app.register_blueprint(site.routes.atlas.module, url_prefix='/')
app.register_blueprint(site.routes.home.module, url_prefix='/')
app.register_blueprint(site.routes.governance.module, url_prefix='/')
app.register_blueprint(site.routes.dataset_search.module, url_prefix='/')
app.register_blueprint(site.routes.dataset_upload.module, url_prefix='/')

