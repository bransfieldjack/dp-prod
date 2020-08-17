import flask
import os
import jwt
import datetime # Using datetime to facilitate JWT token expiration. 
from smtplib import SMTP
from flask import Flask, session, Blueprint, render_template, request, Response, redirect, url_for, jsonify
from app.api.models import datasets, UserModel, _runSql
from flask_login import login_user
from app import app
from functools import wraps
from flask_cors import CORS, cross_origin


module = Blueprint('api_login', __name__)


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.args.get('token')

        if not token:
            return jsonify({'message': 'Token is missing!'}), 403

        try: 
            jwt.decode(token, app.config['SECRET_KEY'])
        except:
            return jsonify({'Message': 'Missing or invalid token.'}), 403
        
        return f(*args, **kwargs)

    return decorated


@module.route('/dataportal')
def api_login_page():
    """
    Renders the Dataportal login page. 
    """
    return render_template('/api/api_login.html')


@module.route('/jwt_token')
def api_jwt_token_page():
    """
    Renders the jwt_token page. 
    """
    return render_template('/api/token.html')


@module.route('/frontend_auth', methods=['GET', 'POST'])
@cross_origin(origin='*',headers=['Content-Type','Authorization'])
def frontend_auth():
    """
    Auth access for front end apps.
    """
    payload = request.get_json()
    username = payload["username"]
    password = payload["password"]

    # print(username)
    # print(password)
    
    # return {
    #     "username": username,
    #     "password": password
    # }

    _username = UserModel.User(username)
    auth = _username.authenticate(username, password)

    if auth == True:
        token = jwt.encode({"user": username, "password": password, "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'])  #  Expiration is a reserved part of the payload in JWT
        return {
            'token': token.decode('UTF-8'),
            'message': 'authorized'
            }
    if auth != True:
        return {'message': 'not authorized'}


@module.route('/api_jwt_token_generated', methods=['GET', 'POST'])
def api_jwt_token_generated():
    """
    Generates the jwt_token. 
    """
    
    username = request.form['username']
    password = request.form['password']

    _username = UserModel.User(username)
    auth = _username.authenticate(username, password)

    if auth == True:
        token = jwt.encode({"user": username, "password": password, "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'])  #  Expiration is a reserved part of the payload in JWT
        return {'token': token.decode('UTF-8')}
    if auth != True:
        return {'message': 'not authorized'}
 


@module.route('/login_error')
def api_login_error():
    """
    Renders a login error page, other methods will redirect to here. 
    """
    return render_template('/api/login_error.html')


@module.route('/login', methods=['GET', 'POST'])
def api_login():
    """

    This handles logging into the dataportal. 
    The method will check that the user information is valid
    and store the user session information.

    After the user is logged in a JWT token is returned. 
    The token can then be used on any subsequent requests. 

    The API will auto-verify that the token is valid.
    Token expiry will be set to 30mins by default, after which the user will need to login again. 

    """
    username = request.form['login']
    password = request.form['password']

    """
    Handle auth:
    """

    auth = UserModel
    _hash = auth.hash_password(password)
    _verify = auth.verify_password(password, _hash) # Will return true/false is the password doesnt already exist. 
    loggedIn =  str(_verify)

    _username = UserModel.User(username)
    session["user"] = username
    session["loggedIn"] = True

    role = _username.role(username)
    session["role"] = role

    if role == 'admin':
        session["admin"] = True
    else:
        session["admin"] = False

    auth = _username.authenticate(username, password)

    """
    Handle conditional redirect:
    """

    if auth == True:
        if session["user"] == username:
            if session["loggedIn"] == True:
                admin = session["admin"]
                token = jwt.encode({"user": username, "password": password, "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'])  #  Expiration is a reserved part of the payload in JWT
                return redirect(url_for('home.home', auth=auth, admin=admin, token=token.decode('UTF-8')))
    if auth != True:
        return redirect('/login_error')


@module.route('/api_logout', methods=['GET', 'POST'])
def api_logout():
    """
    Handles removing the session information for the user and redirection to the login page. 
    """
    session.pop("user", None)
    session["loggedIn"] = False
    return redirect(url_for('api_login.api_login_page'))

