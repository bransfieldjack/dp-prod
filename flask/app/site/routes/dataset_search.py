import flask
from flask import session
from smtplib import SMTP
from flask import Flask, Blueprint, render_template, request, Response, redirect, url_for, jsonify
from app.api.models import datasets, UserModel, _runSql
import numpy


module = Blueprint('dataset_search', __name__)


@module.route("/samples_grid", methods=['GET', 'POST'])
def samples_grid():
    data = request.get_json()
    dataset_id = data['dataset_id']
    ds = datasets.Dataset(dataset_id)
    sampleTable = ds.sampleTable()
    jsonSampleTable = sampleTable.to_json(orient="split")

    if session["loggedIn"] == True:
        if jsonSampleTable != None:
            return jsonSampleTable
        else:
            return {"Message": "No samples found for dataset_id: " + dataset_id}
    else:
        return "Access Denied"


@module.route("/atlas_samples_grid", methods=['GET', 'POST'])
def atlas_samples_grid():

    data = request.get_json()
    atlas_type = data['atlas_type']
    atlas_model = atlas_type['atlas_model']
    atlas_project = atlas_type['tierModel']
    update_column = atlas_model + '_' + atlas_project
    dataset_id = data['dataset_id']
    ds = datasets.Dataset(dataset_id)
    atlasSampleTable = ds.atlasSampleTable()
    
    newdf = atlasSampleTable[['sample_id'] + [update_column] + ['annotator', 'evidence', 'phenotype', 'activation_status', 'display_metadata', 'include_blood', 'include_imac'] ]    # construct a dataframe with the selected tier included in it. 
        
    include_blood = newdf['include_blood'].unique()
    include_imac = newdf['include_imac'].unique()

    if include_blood[0] == False:
        print("drop all blood tier data")

        # finaldf = atlasSampleTable[['sample_id'] + [update_column] + ['annotator', 'evidence', 'phenotype', 'activation_status', 'display_metadata', 'include_blood', 'include_imac'] ]

    elif include_imac[0] == False:
        print("drop all imac tier data")

    elif include_blood[0] and include_imac[0] == False:
        print("drop all tier data")

    elif include_blood[0] and include_imac[0] == True:
        print("include all tier data")

    
    jsonSampleTable = newdf.to_json(orient="split")

    if session["loggedIn"] == True:
        return jsonSampleTable
    else:
        return "Access Denied"


