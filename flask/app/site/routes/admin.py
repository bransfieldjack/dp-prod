import flask
import os
from smtplib import SMTP
from flask import Flask, session, Blueprint, render_template, request, Response, redirect, url_for, jsonify
from app.api.models import datasets, UserModel, _runSql


module = Blueprint('admin', __name__)


@module.route('/admin', methods=['GET', 'POST'])
def admin():

    if session["admin"] == True:
        user = session["user"]
        return render_template('/api/admin_panel.html', user=user)
    else:
        return redirect('/login_error')


@module.route('/user_update', methods=['GET', 'POST'])
def user_update():
    data = request.get_json()
    payload = data['data']
    username = payload['username']
    password = payload['password']
    verifyPassword = payload['verifyPassword']
    role = payload['role']
    user = UserModel.User(username)
    update = user.update(username, password, role)
    return {"updated": "true"}


@module.route('/add_user', methods=['GET', 'POST'])
def add_user():
    data = request.get_json()
    payload = data['data']
    email = payload['email']
    role = payload['role']
    password = payload['password']
    user = UserModel.User(email)
    create = user.create(email, password, role)
    return {"created": create}


@module.route('/delete_user', methods=['GET', 'POST'])
def delete_user():
    data = request.get_json()
    payload = data['data']
    username = payload['username']
    user = UserModel.User(username)
    delete = user.delete(username)
    return {"deleted": delete}

    
