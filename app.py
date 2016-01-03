from flask import Flask  
from flask import render_template  
from flask import request
from flask import abort
from flask import redirect
from flask import url_for
from flask import session
from flask import g
from flask_socketio import SocketIO
from flask_socketio import join_room, leave_room
from bidict import bidict

import os
import challonge
import brawlapi

# Bi-directional map from tournament's Challonge URL suffix to its ID.
# We'll actually build this from the Challonge API later.
tourneys = bidict({ 'thelastbanana_test': '2119181' })
tourneyDatas = {}

# Set of online participant IDs
onlineUsers = set()

challonge.set_credentials(os.environ.get('BB_CHALLONGE_USER'), os.environ.get('BB_CHALLONGE_API_KEY'))

app = Flask(__name__)
app.secret_key = os.environ.get('BB_SECRET_KEY')
socketio = SocketIO(app)

    
#----- Flask routing -----#
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route('/')
@app.route('/index/')
def index():
    return render_template('index.html')
    brawlapi.init_example_db()

# Log in a tourney participant
@app.route('/<tourneyName>/', methods=['GET', 'POST'])
def user_login(tourneyName):
    if tourneyName not in tourneys:
        abort(404)

    tourneyId = tourneys[tourneyName]
    
    if request.method == 'GET':
        
        # This should request from the database after checking the memory cache
        # and before going to Challonge
        if tourneyId not in tourneyDatas:
            tourneyData = challonge.tournaments.show(tourneyId)
            tourneyDatas[tourneyId] = tourneyData
        else:
            tourneyData = tourneyDatas[tourneyId]
        
        prettyName = tourneyData['name']
        tourneyURL = tourneyData['full-challonge-url']
        
        participantData = challonge.participants.index(tourneyId)
        # Boolean value is whether the user is already logged in
        participants = [ (p['name'], p['id'], False) for p in participantData ]

        return render_template('user-login.html',
                               tourneyName=prettyName,
                               participants=participants,
                               challongeURL=tourneyURL)
   
    # POST was used
    # TODO: validate user ID
    userId = request.form['user']
    session['participantId'] = userId
    session['tourneyId'] = tourneyId
    
    return redirect(url_for('user_landing', tourneyName=tourneyName))

# User app page
@app.route('/<tourneyName>/app/')
def user_landing(tourneyName):
    return render_template('user-app.html')
    
# Lobby content
@app.route('/lobby')
def lobby():
    return render_template('lobby.html')

    
#----- SocketIO events -----#
@socketio.on('connect', namespace='/participant')
def participant_connect():
    pId = session.get('participantId')
    tId = session.get('tourneyId')
    
    if not pId:
        print('Participant id missing; connection rejected')
        return False
    
    if pId in onlineUsers:
        print('Participant #{} rejected (already connected)'.format(pId))
        return False
        
    onlineUsers.add(pId)
    
    # Leave old room
    if 'matchId' in session:
        print('Participant #{} connecting, left old room #{}'
            .format(pId, session['matchId']))
        leave_room(str(session['matchId']))
    
    # Find current match
    matchesData = challonge.matches.index(tId)
    matchData = None
    for match in matchesData:
        print(pId, match['player1-id'], match['player2-id'], type(match['winner-id']))
        if int(pId) in [match['player1-id'], match['player2-id']] \
                and match['winner-id'] is None:
            matchData = match
            break
    
    # Join new room
    session['matchId'] = matchData['id']
    join_room(str(matchData['id']))
    
    print('Participant #{} connected, joined room #{}'
        .format(pId, matchData['id']))
    
@socketio.on('disconnect', namespace='/participant')
def participant_disconnect():
    pId = session.get('participantId')
    
    # No pId, so we're not online anyway
    if pId == None:
        return
    
    onlineUsers.remove(pId)

    print('Participant disconnected')

if __name__ == '__main__':
    app.debug = True
    socketio.run(app)