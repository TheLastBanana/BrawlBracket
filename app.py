from flask import Flask  
from flask import render_template  
from flask import request
from flask import abort
from flask import redirect
from flask import url_for
import flask.ext.login as flask_login
from bidict import bidict

import os
import challonge
import brawlapi

class User(flask_login.UserMixin):
    def __init__(self, id):
        self.id = id

# Bi-directional map from tournament's Challonge URL suffix to its ID.
# We'll actually build this from the Challonge API later.
tourneys = bidict({ 'thelastbanana_test': '2119181' })

# User data from Challonge participant id
onlineUsers = {}

challonge.set_credentials(os.environ.get('BB_CHALLONGE_USER'), os.environ.get('BB_CHALLONGE_API_KEY'))

app = Flask(__name__)
app.secret_key = os.environ.get('BB_SECRET_KEY')

login_manager = flask_login.LoginManager()
login_manager.login_view = 'index'
login_manager.init_app(app)

@login_manager.user_loader
def user_loader(user_id):
    return onlineUsers.get(user_id)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')
    brawlapi.init_example_db()

# Log in a tourney participant
@app.route('/login/<tourneyName>', methods=['GET', 'POST'])
def user_login(tourneyName):
    if tourneyName not in tourneys:
        abort(404)

    if request.method == 'GET':
        tourneyId = tourneys[tourneyName]
        tourneyData = challonge.tournaments.show(tourneyId)
        prettyName = tourneyData['name']
        tourneyURL = tourneyData['full-challonge-url']
        
        participantData = challonge.participants.index(tourneyId)
        # Boolean value is whether the user is already logged in
        participants = [ (p['name'], p['id'], False) for p in participantData ]

        return render_template('user-login.html',
                               tourneyName=prettyName,
                               participants=participants,
                               challongeURL=tourneyURL)
   
    elif request.method == 'POST':
        userId = request.form['user']
        user = User(userId)
        onlineUsers[userId] = user
        flask_login.login_user(user)
        
        return redirect(url_for('user_landing', tourneyName=tourneyName))

# User landing page
@app.route('/app/<tourneyName>/user/')
@flask_login.login_required
def user_landing(tourneyName):
    if request.method == 'GET':
        return 'Please implement me!'
        
    return render_template('user-landing.html')

if __name__ == '__main__':
    app.debug = True
    app.run()