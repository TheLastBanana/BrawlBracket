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
from flask_socketio import emit
from bidict import bidict

import os
import brawlapi

# Mapping from legend id to (formatted name, internal name)
legendData = {
    0:      ('Random',      'random'),
    1:      ('Bödvar',      'bodvar'),
    2:      ('Cassidy',     'cassidy'),
    3:      ('Orion',       'orion'),
    4:      ('Lord Vraxx',  'vraxx'),
    5:      ('Gnash',       'gnash'),
    6:      ('Nai',         'nai'),
    7:      ('Hattori',     'hattori'),
    8:      ('Sir Roland',  'roland'),
    9:      ('Scarlet',     'scarlet'),
    10:     ('Thatch',      'thatch'),
    11:     ('Ada',         'ada'),
    12:     ('Sentinel',    'sentinel'),
    13:     ('Lucien',      'lucien'),
    14:     ('Teros',       'teros'),
    15:     ('Brynn',       'brynn'),
    16:     ('Asuri',       'asuri'),
    17:     ('Barraza',     'barraza'),
    18:     ('Ember',       'ember'),
    19:     ('Azoth',       'azoth')
}
legendOrder = list(range(1, len(legendData))) + [0] # Always put random last
orderedLegends = [legendData[id] for id in legendOrder]

realmData = {
    0:      ('Random',                  'random'),
    1:      ('Brawlhaven',              'brawlhaven'),
    2:      ('Grumpy Temple',           'grumpy'),
    3:      ('Twilight Grove',          'twilight'),
    4:      ('Kings Pass',              'kings'),
    5:      ('Thundergard Stadium',     'thunder'),
    6:      ('Titan\'s End',            'titan'),
    7:      ('Blackguard Keep',         'keep'),
    8:      ('The Enigma',              'enigma'),
    9:      ('Mammoth Fortress',        'mammoth'),
    10:     ('Great Hall',              'hall'),
    11:     ('Shipwreck Falls',         'falls'),
    12:     ('Big Great Hall',          'big-hall'),
    13:     ('Big Kings Pass',          'big-kings'),
    14:     ('Big Thundergard Stadium', 'big-thunder'),
    15:     ('Big Titan\'s End',        'big-titan'),
    16:     ('Big Twilight Grove',      'big-twilight'),
    17:     ('Bombsketball',            'bombsketball'),
    18:     ('Brawlball',               'brawlball'),
    19:     ('Wally',                   'wally'),
    20:     ('Short Side',              'short'),
    21:     ('Pillars',                 'pillars'),
}
eslRealms = [3, 4, 5, 7, 9, 10, 11]
orderedRealms = [realmData[id] for id in eslRealms]

# Bi-directional map from tournament's Challonge URL suffix to its ID.
# We'll actually build this from the Challonge API later.
tourneys = bidict({ 'thelastbanana_test': '2119181' })

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
        prettyName = brawlapi.getTournamentName(tourneyId)
        tourneyURL = brawlapi.getTournamentURL(tourneyId)
        
        participantData = brawlapi.getParticipants(tourneyId)
        # Boolean value is whether the user is already logged in
        participants = [(p[0], p[1], 
                        brawlapi.isUserOnline(int(p[1])))
                            for p in participantData]

        return render_template('user-login.html',
                               tourneyName=prettyName,
                               participants=participants,
                               challongeURL=tourneyURL)
   
    # POST was used
    # TODO: validate user ID
    participantId = request.form['user']
    session['participantId'] = participantId
    session['tourneyId'] = tourneyId
    
    return redirect(url_for('user_landing', tourneyName=tourneyName))

# User app page
@app.route('/<tourneyName>/app/')
def user_landing(tourneyName):
    return render_template('user-app.html')
    
# Lobby content
@app.route('/app-content/lobby')
def lobby():
    return render_template('app-content/lobby.html')
    
# Lobby connect error
@app.route('/app-content/lobby-error')
def lobby_error():
    return render_template('app-content/lobby-error.html')
    
# Lobby legend roster
@app.route('/app-content/lobby-roster')
def lobby_roster():
    return render_template('app-content/lobby-roster.html', legendData=orderedLegends)
    
# Lobby map picker
@app.route('/app-content/lobby-realms')
def lobby_realm():
    return render_template('app-content/lobby-realms.html', realmData=orderedRealms)

    
#----- SocketIO events -----#
@socketio.on('connect', namespace='/participant')
def participant_connect():
    pId = session.get('participantId')
    tId = session.get('tourneyId')
    
    if not pId:
        print('Participant id missing; connection rejected')
        emit('error', {'code': 'bad-participant'},
            broadcast=False, include_self=True)
        return False
    
    if brawlapi.isUserOnline(pId):
        print('Participant #{} rejected (already connected)'.format(pId))
        emit('error', {'code': 'already-connected'},
            broadcast=False, include_self=True)
        return False
    
    brawlapi.addOnlineUser(pId)
    
    # Find current match
    matchId = brawlapi.getParticipantMatch(tId, pId)
        
    # Handle no match found
    if matchId is None:
        print('Participant #{} connected but found no match.'.format(pId))
        emit('error', {'code': 'no-match'},
            broadcast=False, include_self=True)
        return False
    
    # Join new room
    session['matchId'] = matchId
    join_room(str(matchId))
    
    print('Participant #{} connected, joined room #{}'
        .format(pId, matchId))
        
    lobbyData = brawlapi.getLobbyData(tId, matchId)
        
    emit('join lobby', lobbyData,
        broadcast=False, include_self=True)
    
@socketio.on('disconnect', namespace='/participant')
def participant_disconnect():
    pId = session.get('participantId')
    
    # No pId, so we're not online anyway
    if pId == None:
        return
    
    brawlapi.removeOnlineUser(pId)

    print('Participant #{} disconnected'.format(pId))

# A participant win was reported
@socketio.on('report win', namespace='/participant')
def participant_report_win(data):
    print('{} won a match'.format(data['player-id']))

if __name__ == '__main__':
    app.debug = True
    socketio.run(app)