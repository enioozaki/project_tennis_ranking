from flask import (Flask, render_template, request, redirect, jsonify,
                   url_for, flash)
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Club, Associate, User
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Club Association Application"


# Connect to Database and create database session
engine = create_engine('sqlite:///clubs.db?check_same_thread=False')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "access token received %s " % access_token

    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type='\
        'fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token='\
        '%s' % (app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.8/me"
    token = result.split(',')[0].split(':')[1].replace('"', '')

    url = 'https://graph.facebook.com/v2.8/me?access_token=%s&fields=name,'\
        'id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    print "url sent for API access:%s" % url
    print "API JSON result: %s" % result
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data['name']
    login_session['email'] = data['email']
    login_session['facebook_id'] = data['id']

    # The token must be stored in the login_session in order to properly logout
    login_session['access_token'] = token

    # Get user picture
    url = 'https://graph.facebook.com/v2.8/me/picture?access_token='\
        '%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Bem-vindo, '
    output += login_session['username']

    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius:'\
        ' 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '

    flash("Logado como %s" % login_session['username'])
    return output


@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token='\
        '%s' % (facebook_id, access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "usuario foi deslogado"


@app.route('/gconnect', methods=['POST'])
def gconnect():
    print '---gconnect---'
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code

    access_token = json.loads(request.data)["token"]
    credentials = json.loads(request.data)['profile']
    jsonobj = json.loads(request.data)
    # Check that the access token is valid.

    url = ('https://oauth2.googleapis.com/tokeninfo?id_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])

    try:
        if result['iss'] not in ['accounts.google.com',
                                 'https://accounts.google.com']:
            raise ValueError('Wrong issuer.')
        # ID token is valid.
        # Get the user's Google Account ID from the decoded token.
        userid = result['sub']
    except ValueError:
        # Invalid token
        pass
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials["Eea"]
    if userid != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['aud'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response
    # Store the access token in the session for later use.
    login_session['access_token'] = access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    login_session['username'] = result['name']
    login_session['picture'] = result['picture']
    login_session['email'] = result['email']

    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(result["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Bem-vindo, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius:'\
        ' 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("voce esta logado como %s" % login_session['username'])
    print "done!"
    return output

# User Helper Functions


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

# DISCONNECT - Revoke a current user's token and reset their login_session


@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    access_token = login_session['access_token']
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        response = make_response(json.dumps('Desconectado com sucesso.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps(
            'Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# JSON APIs to view Club Information
@app.route('/club/<int:club_id>/associates/JSON')
def clubAssociatesJSON(club_id):
    club = session.query(Club).filter_by(id=club_id).one()
    items = session.query(Associate).filter_by(
        club_id=club_id).all()
    return jsonify(Associates=[i.serialize for i in items])


@app.route('/club/<int:club_id>/associate/<int:associate_id>/JSON')
def associateJSON(club_id, associate_id):
    Associate = session.query(Associate).filter_by(id=associate_id).one()
    return jsonify(Associate=Associate.serialize)


@app.route('/club/JSON')
def clubsJSON():
    clubs = session.query(Club).all()
    print jsonify(clubs=[r.serialize for r in clubs])
    return jsonify(clubs=[r.serialize for r in clubs])


# Show all clubs
@app.route('/')
@app.route('/club/')
def showClubs():
    clubs = session.query(Club).order_by(asc(Club.name))
    if 'username' not in login_session:
        return render_template('publicClubs.html', clubs=clubs)
    else:
        return render_template('clubs.html', clubs=clubs)


# Create a new club
@app.route('/club/new/', methods=['GET', 'POST'])
def newClub():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newClub = Club(
            name=request.form['name'], user_id=login_session['user_id'])
        session.add(newClub)
        flash('Novo Clube %s Criado com Sucesso' % newClub.name)
        session.commit()
        return redirect(url_for('showClubs'))
    else:
        return render_template('newClub.html')


# Edit a club
@app.route('/club/<int:club_id>/edit/', methods=['GET', 'POST'])
def editClub(club_id):
    editedClub = session.query(
        Club).filter_by(id=club_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if editedClub.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized"\
            " to edit this club. Please create your own club in order to "\
            "edit.');}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        if request.form['name']:
            editedClub.name = request.form['name']
            flash('Clube Editado com Sucesso %s' % editedClub.name)
            return redirect(url_for('showClubs'))
    else:
        return render_template('editClub.html', club=editedClub)


# Delete a club
@app.route('/club/<int:club_id>/delete/', methods=['GET', 'POST'])
def deleteClub(club_id):
    clubToDelete = session.query(
        Club).filter_by(id=club_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if clubToDelete.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert("\
            "'You are not authorized to delete this club. "\
            "Please create your own club in order to delete.'"\
            ");}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        session.delete(clubToDelete)
        flash('%s Removido com Sucesso' % clubToDelete.name)
        session.commit()
        return redirect(url_for('showClubs', club_id=club_id))
    else:
        return render_template('deleteClub.html', club=clubToDelete)


# Show a club associate
@app.route('/club/<int:club_id>/')
@app.route('/club/<int:club_id>/associate/')
def showAssociate(club_id):
    club = session.query(Club).filter_by(id=club_id).one()
    creator = getUserInfo(club.user_id)
    items = session.query(Associate).filter_by(
        club_id=club_id).all()
    print "creator", creator.name
    print "login_session", login_session
    if ('username' not in login_session or
            creator.id != login_session['user_id']):
        return render_template('publicAssociates.html', items=items,
                               club=club, creator=creator)
    else:
        return render_template('associate.html', items=items, club=club,
                               creator=creator)


# Create a new associate item
@app.route('/club/<int:club_id>/associate/new/', methods=['GET', 'POST'])
def newAssociate(club_id):
    if 'username' not in login_session:
        return redirect('/login')
    club = session.query(Club).filter_by(id=club_id).first()
    if login_session['user_id'] != club.user_id:
        return "<script>function myFunction() {alert('You are not authorized"\
            " to add associate items to this club. Please create your own "\
            "club in order to add items.');}</script><body onload="\
            "'myFunction()'>"
    if request.method == 'POST':
            newItem = Associate(name=request.form['name'],
                                gender=request.form['gender'],
                                birthDate=request.form['birthDate'],
                                classe=request.form['classe'],
                                ranking=request.form['ranking'],
                                points=request.form['points'],
                                club_id=club_id,
                                user_id=club.user_id)
            session.add(newItem)
            session.commit()
            flash('Novo Associado %s Criado com Sucesso' % (newItem.name))
            return redirect(url_for('showAssociate', club_id=club_id))
    else:
        return render_template('newAssociate.html', club_id=club_id)


# Edit an associate item
@app.route('/club/<int:club_id>/associate/<int:associate_id>/edit',
           methods=['GET', 'POST'])
def editAssociate(club_id, associate_id):
    if 'username' not in login_session:
        return redirect('/login')
    editedItem = session.query(Associate).filter_by(id=associate_id).one()
    club = session.query(Club).filter_by(id=club_id).one()
    if login_session['user_id'] != club.user_id:
        return "<script>function myFunction() {alert('You are not authorized"\
            " to edit associate items to this club. Please create your own "\
            "club in order to edit items.');}</script><body onload="\
            "'myFunction()'>"
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['gender']:
            editedItem.gender = request.form['gender']
        if request.form['birthDate']:
            editedItem.birthDate = request.form['birthDate']
        if request.form['classe']:
            editedItem.classe = request.form['classe']
        if request.form['ranking']:
            editedItem.ranking = request.form['ranking']
        if request.form['points']:
            editedItem.points = request.form['points']
        flash('Associado Editado com Sucesso')
        return redirect(url_for('showAssociate', club_id=club_id))
    else:
        return render_template('editAssociate.html', club_id=club_id,
                               associate_id=associate_id,
                               associate=editedItem)


# Delete a associate item
@app.route('/club/<int:club_id>/associate/<int:associate_id>/delete',
           methods=['GET', 'POST'])
def deleteAssociate(club_id, associate_id):
    if 'username' not in login_session:
        return redirect('/login')
    club = session.query(Club).filter_by(id=club_id).one()
    itemToDelete = session.query(Associate).filter_by(id=associate_id).one()
    if login_session['user_id'] != club.user_id:
        return "<script>function myFunction() {alert('You are not authorized"\
            " to delete associate items to this club. Please create your own"\
            " club in order to delete items.');}</script><body onload="\
            "'myFunction()'>"
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash('Associado Removido com Sucesso')
        return redirect(url_for('showAssociate', club_id=club_id))
    else:
        return render_template('deleteAssociate.html', associate=itemToDelete,
                               club_id=club_id)


# Disconnect based on provider
@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['access_token']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("Voce foi deslogado com sucesso.")
        return redirect(url_for('showClubs'))
    else:
        flash("Voce nao foi logado")
        return redirect(url_for('showClubs'))


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
