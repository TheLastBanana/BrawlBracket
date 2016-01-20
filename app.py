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
import challonge
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

# Cached Challonge data
tourneyDatas = {}
matchDatas = {}
participantDatas = {}

# Data for each lobby
lobbyDatas = {}

# Set of online participant IDs
onlineUsers = set()

challonge.set_credentials(os.environ.get('BB_CHALLONGE_USER'), os.environ.get('BB_CHALLONGE_API_KEY'))

app = Flask(__name__)
app.secret_key = os.environ.get('BB_SECRET_KEY')
socketio = SocketIO(app)


# Get data for a match. If matchId is None, returns the match index.
# TODO: Fetch this data more than once so it can update
def getMatchData(tourneyId, matchId = None):
    if tourneyId not in matchDatas \
            or matchId not in matchDatas[tourneyId]:
        tourneyData = {}
        
        mIndex = challonge.matches.index(tourneyId)
        tourneyData[None] = mIndex
        
        for mData in mIndex:
            tourneyData[mData['id']] = mData
            
        matchDatas[tourneyId] = tourneyData
        
    if tourneyId not in matchDatas \
            or matchId not in matchDatas[tourneyId]:
        return None

    return matchDatas[tourneyId][matchId]

# Get data for a participant. If participantId is None, returns the match index.
# TODO: Fetch this data more than once so it can update
def getParticipantData(tourneyId, participantId = None):
    if tourneyId not in participantDatas \
            or participantId not in participantDatas[tourneyId]:
        tourneyData = {}
        
        pIndex = challonge.participants.index(tourneyId)
        tourneyData[None] = pIndex
        
        for pData in pIndex:
            tourneyData[pData['id']] = pData
            
        participantDatas[tourneyId] = tourneyData
        
    if tourneyId not in participantDatas \
            or participantId not in participantDatas[tourneyId]:
        return None

    return participantDatas[tourneyId][participantId]

# Get lobby data for a given match, or if it doesn't exist, create it and store it in lobbyDatas.
def getLobbyData(tourneyId, matchId):
    matchPair = (tourneyId, matchId)
    
    #if matchPair in lobbyDatas:
    #    return lobbyDatas[matchPair]

    # Not found, so make a new lobby
    matchData = getMatchData(tourneyId, matchId)

    # Get participant info
    p1Id = matchData['player1-id']
    p2Id = matchData['player2-id']
    p1Data = getParticipantData(tourneyId, p1Id)
    p2Data = getParticipantData(tourneyId, p2Id)
    
    gravatarBase = 'http://www.gravatar.com/avatar/{}?d=identicon'
        
    lobbyData = {
        'participants': [
            {
                'name': playerData['display-name'],
                'id': playerData['id'],
                'seed': playerData['seed'],
                'ready': False,
                'wins': 0,
                
                # Note the 'or' here. If the player has no email hash, 
                # we use their participant ID as a unique Gravatar hash.
                'avatar': gravatarBase.format(playerData['email-hash'] or p1Id)
            } for playerData in [p1Data, p2Data]
        ],
        
        # Players are individual users, while participants may be teams (though we don't support them yet).
        # For now, they're basically the same, but this field holds data that would only apply to one person.
        'players': [
            {
                'name': playerData['display-name'],
                'status': 'Online' if playerData['id'] in onlineUsers else 'Offline',
                'legend': 'none'
            } for playerData in [p1Data, p2Data]
        ],
        
        # This is a dictionary in case it needs to hold state-specific data later
        'state': {
            'name': 'waitingForPlayers'
        },
        
        'chatlog': [],
        'realmBans': [],
        
        'roomNumber': None,
        'currentRealm': None
    }
    
    lobbyDatas[matchPair] = lobbyData
    
    return lobbyData
    
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
    
    if pId in onlineUsers:
        print('Participant #{} rejected (already connected)'.format(pId))
        emit('error', {'code': 'already-connected'},
            broadcast=False, include_self=True)
        return False
        
    onlineUsers.add(int(pId))
    
    # Find current match
    matchesData = getMatchData(tId)
    matchId = None
    for match in matchesData:
        if int(pId) in (match['player1-id'], match['player2-id']) \
                and match['winner-id'] is None \
                and None not in (match['player1-id'], match['player2-id']):
            matchId = match['id']
            break
        
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
        
    lobbyData = getLobbyData(tId, matchId)
        
    emit('join lobby', lobbyData)
    
@socketio.on('disconnect', namespace='/participant')
def participant_disconnect():
    pId = session.get('participantId')
    
    # No pId, so we're not online anyway
    if pId == None:
        return
    
    onlineUsers.remove(int(pId))

    print('Participant disconnected')

# A participant win was reported
@socketio.on('report win', namespace='/participant')
def participant_report_win(data):
    print('{} won a match'.format(data['player-id']))

if __name__ == '__main__':
    app.debug = True
    socketio.run(app)