from app import app, db, auth
from datetime import datetime
import errno
from flask import abort, flash, g, jsonify, make_response, redirect, render_template, request, session, url_for, send_from_directory
from flask.ext.login import current_user, login_required, login_user, logout_user
from .forms import UserLoginForm, UserRegisterForm
import os
from .models import Company, User
import math
import random
import re

def verifyRegistration(name, email, email_check, age, password = True):
	if not User.verify_username(name):
		return "Name Must Include 2+ Letters, Spacing, or Punctuation."
	if not User.verify_email(email):
		return "Email Address Is Incorrect."
	if email_check:
		if not User.verify_unique_email(email):
			return "Email Address Is Already Registered."
	if not User.verify_age(age):
		return "Users Must Be Older Than 12 Years Old."
	if password != True:
		if not User.verify_password(password):
			return "Password Must Be 6+ Characters."
	return True

def get_deals(lat, lng, radius):
	center = (lat, lng)
	return Company.nearby_companies(center, radius)

# Authentication Decorators
@auth.verify_password
def verify_password(email, password):
	# Works because passwords must be 6 chars by client-side verification
	if password == "token":
		user = User.verify_token(email)
		if user is None:
			return False
		g.user = user
		return True
	else:
		user = User.query.filter_by(email = email).first()
		if not user or not user.check_password(password):
			return False
		g.user = user
		return True

@auth.error_handler
def unauthorized():
	return make_response(jsonify({'error': 'Unauthorized Access'}), 401)

# Returns Current Version's URI
@app.route('/mobile/api', methods = ['GET'])
def ApiCurrentVersion():
	return jsonify({'uri':'/mobile/api/v0.1/'})

# Where Login Page Should Route To
@app.route('/mobile/api/v0.1/token', methods = ['POST'])
@auth.login_required
def ApiLogin():
	token = g.user.generate_token()
	return jsonify({'token': token, 'user_id': g.user.id}), 200

# Where Register Page Should Route To
@app.route('/mobile/api/v0.1/users', methods = ['POST'])
def ApiRegister():
	username = request.json.get('name')
	email = request.json.get('email')
	age = request.json.get('age')
	password = request.json.get('password')
	error = verifyRegistration(username, email, True, age, password)
	if error != True:
		return make_response(jsonify({'error':'Bad Request', 'message': error}), 400)
	user = User(username = username, email = email, age = age)
	user.add_password(password)
	db.session.add(user)
	db.session.commit()
	token = user.generate_token()
	return jsonify({'token': token, 'user_id': user.id}), 201

# Where Settings Page Should Route To
@app.route('/mobile/api/v0.1/users/<int:id>', methods = ['GET'])
@auth.login_required
def ApiGetUser(id):
	if g.user.id != id:
		return make_response(jsonify({'error':'Forbidden'}), 403)
	username = g.user.username
	email = g.user.email
	age = g.user.age
	return jsonify({'username': username, 'email': email, 'age': age}), 200

# Where Settings Page Submit Should Route To
@app.route('/mobile/api/v0.1/users/<int:id>', methods = ['PUT'])
@auth.login_required
def ApiUpdateUser(id):
	if g.user.id != id:
		return make_response(jsonify({'error':'Forbidden'}), 403)
	username = request.json.get('name')
	email = request.json.get('email')
	age = request.json.get('age')
	email_check = True
	if email == g.user.email:
		email_check = False
	error = verifyRegistration(username, email, email_check, age)
	if error != True:
		return make_response(jsonify({'error':'Bad Request', 'message':error}), 400)
	g.user.username = username
	g.user.email = email
	g.user.age = age
	password = request.json.get('password')
	if User.verify_password(password):
		g.user.add_password(password)
	db.session.add(g.user)
	db.session.commit()
	token = g.user.generate_token()
	return jsonify({'token': token}), 200

# Where Map Page Should Route To
@app.route('/mobile/api/v0.1/users/<int:id>/map', methods = ['GET', 'PUT'])
@auth.login_required
def ApiUploadMap(id):
	if g.user.id != id:
		return make_response(jsonify({'error':'Forbidden'}), 403)
	if request.json:
		lat = request.json.get('lat')
		lng = request.json.get('lng')
	else:
		lat = request.args.get('lat')
		lng = request.args.get('lng')
	if lat is None or lng is None:
		return make_response(jsonify({'error':'Bad Request'}), 400)
	try:
		lat = float(lat)
		lng = float(lng)
	except ValueError:
		return make_response(jsonify({'error':'Bad Values'}), 400)
	deals = get_deals(lat, lng, 0.5)
	return jsonify({'deals': deals}), 200

# Where Company Page Should Route To
@app.route('/mobile/api/v0.1/users/<int:id>/map/<int:companyid>', methods = ['GET'])
@auth.login_required
def ApiCompanyPage(id, companyid):
	if g.user.id != id:
		return make_response(jsonify({'error':'Forbidden'}), 403)
	company = Company.query.get(companyid)
	if not company:
		return make_response(jsonify({'error':'Bad Request'}), 400)
	deal = company.get_deal()
	return jsonify({'deal': deal}), 200

# Where Like/Dislike Deal Should Route To
@app.route('/mobile/api/v0.1/users/<int:id>/map/<int:companyid>', methods = ['PUT'])
@auth.login_required
def ApiPreferenceUpdate(id, companyid):
	if g.user.id != id:
		return make_response(jsonify({'error':'Forbidden'}), 403)
	like = request.json.get('relevant')
	g.user.update_preference(companyid, like)
	db.session.add(g.user)
	db.session.commit()
	return jsonify({'success': True}), 200