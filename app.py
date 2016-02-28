from collections import namedtuple
import uuid
import os
import datetime
import json
import re

from flask import Flask  
from flask import render_template  
from flask import request
from flask import abort
from flask import redirect
from flask import url_for
from flask import session
from flask import g
from flask_socketio import SocketIO
from flask_socketio import join_room, leave_room, rooms
from flask_socketio import emit
from flask.ext.openid import OpenID
from bidict import bidict

import brawlapi
import usermanager as um
import tournamentmanager as tm
import util

__version__ = '0.1.0'

app = Flask(__name__)
app.secret_key = os.environ.get('BB_SECRET_KEY')
socketio = SocketIO(app)
oid = OpenID(app)

_steam_id_re = re.compile('steamcommunity.com/openid/id/(.*?)$')

# Start temp tournament generation
steamIds = [76561198042414835, 76561198078549692, 76561197993702532,
            76561198069178478, 76561198065399638, 76561197995127703,
            76561198068388037, 76561198050490587, 76561198072175457,
            76561198063265824, 76561198042403860]
tempUsers = []
for id in steamIds:
    user = um.getUserBySteamId(id)
    if user is None:
        user = um.createUser(id)
    tempUsers.append(user)
tempTourney = tm.createTournament(
                'test',
                name='BrawlBracket Test Tourney'
                )
for i, user in enumerate(tempUsers):
    team = tempTourney.createTeam(i) # i = seed
    player = tempTourney.createPlayer(user)
    team.players.append(player)
print('Temp tournament has {} users!'.format(len(tempTourney.teams)))
tempTourney.generateMatches()
# End temp tournament generation
    
@app.context_processor
def default_template_data():
    return dict(versionNumber = __version__)
    
#----- Flask routing -----#
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route('/login/')
@oid.loginhandler
def login():
    if session.get('userId', None) is not None:
        return redirect(oid.get_next_url())
    return oid.try_login('http://steamcommunity.com/openid')

@oid.after_login
def createOrLogin(resp):
    match = _steam_id_re.search(resp.identity_url)
    match = int(match.group(1))
    
    user = um.getUserBySteamId(match)
    if user is None:
        user = um.createUser(match)
        
        if user is None:
            print('Couldn\'t make user!')
            return
    
    print(user) # DEBUG
    session['userId'] = user.id
    return redirect(oid.get_next_url())
    
@app.route('/')
@app.route('/index/')
def index():
    userId = session.get('userId', None)
    user = um.getUserById(userId)
    
    userName = user.username if user else None
    userAvatar = user.avatar if user else None
    
    return render_template('index.html',
                           userName=userName,
                           userAvatar=userAvatar)
    brawlapi.init_example_db()

# Log in a tourney participant
@app.route('/t/<tourneyName>/', methods=['GET', 'POST'])
def user_login(tourneyName):
    if not tm.tournamentNameExists(tourneyName):
        abort(404)
    
    if request.method == 'GET':
        pass
        #prettyName = brawlapi.getTournamentName(tourneyId)
        #tourneyURL = brawlapi.getTournamentURL(tourneyId)
        
        #userList = brawlapi.getTournamentUsersOverview(tourneyId)

        #return render_template('app/user-login.html',
        #                       tourneyName=prettyName,
        #                       participants=userList,
        #                       challongeURL=tourneyURL)
   
    # POST was used
    # TODO: validate user ID
    return redirect(url_for('user_app', tourneyName=tourneyName))

#----- User pages -----#

# User app page
@app.route('/t/<tourneyName>/app/', defaults={'startPage': None})
@app.route('/t/<tourneyName>/app/<startPage>/')
def user_app(tourneyName, startPage):
    if not tm.tournamentNameExists(tourneyName):
        abort(404)
    
    userId = session.get('userId', None)
    
    if userId is None:
        print('No userId; returned to login.')
        # TODO: Redirect to the right login
        return redirect(url_for("user_login", tourneyName=tourneyName))
        
    user = um.getUserById(userId)
    if user is None:
        print('User doesn\'t exist; returned to login.')
        # TODO: Redirect to the right login
        return redirect(url_for("user_login", tourneyName=tourneyName))

    tournament = tm.getTournamentByName(tourneyName)
    session['tourneyId'] = tournament.id
    
    
    return render_template('app/user-app.html',
                           startPage=startPage,
                           userName=user.username,
                           userAvatar=user.avatar,
                           tourneyName=tourneyName,
                           tourneyFullName=tournament.name,
                           userId=user.id,
                           basePath='/{}/app/'.format(tourneyName))

# Contact admin page
@app.route('/app-content/contact-admin/<tourneyName>')
def contact_admin(tourneyName):
    return render_template('app/content/contact-admin.html',
                           tourneyFullName=brawlapi.getTournamentName(tourneyName))
    
# Bracket viewer page
@app.route('/app-content/bracket/<tourneyName>')
def bracket(tourneyName):
    tourneyId = tourneys[tourneyName]

    return render_template('app/content/bracket.html',
                           tourneyName=tourneyName,
                           tourneyFullName=brawlapi.getTournamentName(tourneyName),
                           liveImageURL=brawlapi.getTournamentLiveImageURL(tourneyId))
    
# Settings page
@app.route('/app-content/player-settings/<tourneyName>')
def player_settings(tourneyName):
    userId = session.get('userId', None)
    if userId is None:
        print('No userId; returned to login.')
        return redirect(url_for("user_login", tourneyName=tourneyName))
        
    return render_template('app/content/player-settings.html',
                           tourneyFullName=brawlapi.getTournamentName(tourneyName),
                           tourneyName=tourneyName,
                           participantId=session['userId'],
                           legendData=util.orderedLegends,
                           serverRegions=list(util.serverRegions.items()))
    
# Lobby content
@app.route('/app-content/lobby/<tourneyName>')
def lobby(tourneyName):
    tournament = tm.getTournamentByName(tourneyName)
    return render_template('app/content/lobby.html',
                           tourneyFullName=tournament.name)

#----- Admin pages -----#
                           
# Admin app page
@app.route('/t/<tourneyName>/admin/<adminKey>/', defaults={'startPage': None})
@app.route('/t/<tourneyName>/admin/<adminKey>/<startPage>/')
def admin_app(tourneyName, adminKey, startPage):
    tourneyId = tourneys[tourneyName]
    tourneyKeys = brawlapi.adminKeys[tourneyId]
    
    session['adminMode'] = True
    session['participantId'] = -1
    
    # If the key is wrong, don't let the user log in
    if adminKey not in tourneyKeys:
        abort(404)

    return render_template('app/admin-app.html',
                           startPage=startPage,
                           tourneyName=tourneyName,
                           tourneyFullName=brawlapi.getTournamentName(tourneyName),
                           userId=-1,
                           basePath='/{}/admin/{}/'.format(tourneyName, adminKey))
                           
# Admin dashboard
@app.route('/app-content/admin-dashboard/<tourneyName>')
def admin_dashboard(tourneyName):
    tourneyId = tourneys[tourneyName]
    
    # If not an admin, access is denied
    if not session['adminMode']:
        abort(403)

    return render_template('app/content/admin-dashboard.html',
                           liveImageURL=brawlapi.getTournamentLiveImageURL(tourneyId),
                           tourneyFullName=brawlapi.getTournamentName(tourneyName))
    
#----- Page elements -----#
    
# Connect error
@app.route('/app-content/lobby-error/<tourneyName>')
def lobby_error(tourneyName):
    return render_template('app/content/lobby-error.html')
    
# Legend roster
@app.route('/app-content/roster')
def roster():
    return render_template('app/content/lobby-roster.html',
    legendData=util.orderedLegends)
    
# Map picker
@app.route('/app-content/realms')
def realms():
    return render_template('app/content/lobby-realms.html',
                           realmData=util.orderedRealms)

#----- Raw data -----#

# Lobby data
@app.route('/app-data/lobbies/<tourneyName>')
def data_lobbies(tourneyName):
    tourneyId = tourneys[tourneyName]

    # Get a condensed list of lobby data for display to the admin
    condensedData = []
    
    matches = brawlapi.getTournamentMatches(tourneyId)
    for matchId in matches:
        lobbyData = brawlapi.getLobbyData(tourneyId, matchId)
        participants = lobbyData['participants']
        
        # Assemble score string 
        if len(participants) == 2:
            # If there are less than 2 players, this will be either empty or just show one number
            scoreString = '-'.join([str(pData['wins']) for pData in participants])
        else:
            scoreString = '0-0'
            
        # Add on bestOf value (e.g. best of 3)
        scoreString += ' (Bo{})'.format(lobbyData['bestOf'])
        
        status, prettyStatus, statusOrder = brawlapi.getLobbyStatus(tourneyId, matchId)
        
        condensed = {
            'id': lobbyData['challongeId'],
            'p1Name': participants[0]['name'] if len(participants) > 0 else '',
            'p2Name': participants[1]['name'] if len(participants) > 1 else '',
            'score': scoreString,
            'room': lobbyData['roomNumber'] or '',
            'startTime': lobbyData['startTime'] or '',
            'status': {
                'state': lobbyData['state']['name'],
                'display': prettyStatus,
                'sort': statusOrder
            }
        }
        
        condensedData.append(condensed)
        
    ajaxData = {
        'data': condensedData
    }
    
    return json.dumps(ajaxData)
    
# User data
@app.route('/app-data/users/<tourneyName>')
def data_users(tourneyName):
    tourneyId = tourneys[tourneyName]
    
    # Get a condensed list of user data for display to the admin
    condensedData = []
    
    users = brawlapi.getTournamentUsers(tourneyId)
    for user in users:
        status, prettyStatus = brawlapi.getParticipantStatus(tourneyId, user)
        pData = brawlapi.getParticipantData(tourneyId, user.participantId)
        
        condensed = {
            'seed': pData['seed'],
            'name': pData['display-name'],
            'status': {
                'status': status,
                'display': prettyStatus,
            },
            'online': 'Online' if brawlapi.isUserOnline(tourneyId, user) else 'Offline'
        }
        
        condensedData.append(condensed)
        
    ajaxData = {
        'data': condensedData
    }
    
    return json.dumps(ajaxData)
    
    
#----- SocketIO events -----#
@socketio.on('connect', namespace='/participant')
def user_connect():
    userId = session.get('userId', None)
    tourneyId = session.get('tourneyId', None)
    tournament = tm.getTournamentById(tourneyId)
    
    # Weren't passed a userId
    if userId is None:
        print('User id missing; connection rejected')
        emit('error', {'code': 'bad-participant'},
            broadcast=False, include_self=True)
        return False
    
    user = um.getUserById(userId)
    
    # User doesn't exist
    if user is None:
        print('User doesn\'t exist; connection rejected')
        emit('error', {'code': 'bad-participant'},
            broadcast=False, include_self=True)
        return False
    
    info = tournament.getUserInfo(user)
    
    if info is None:
        # TODO: Issue error saying we somehow got into a tournament that
        # we don't live in
        pass
    
    match, team, player = info
    
    if player.online:
        print('User {} rejected (already connected)'
            .format(user.id))
        emit('error', {'code': 'already-connected'},
            broadcast=False, include_self=True)
        return False
    
    player.online = True
    
    # Join new room
    session['matchId'] = match.id
    join_room(match.id)
    
    print('Participant {} connected, joined room #{}'
        .format(user.id, match.id))
    
    # This needs to be done in the /chat namespace, so switch it temporarily
    request.namespace = '/chat'
    join_room(match.chat.getRoom())
    request.namespace = '/participant'
        
    emit('join lobby', {
            'lobbyData': match.getLobbyData(),
            'playerSettings': user.getSettings()
        },
        broadcast=False, include_self=True)
    
@socketio.on('disconnect', namespace='/participant')
def participant_disconnect():
    tourneyId = session.get('tourneyId', None)
    userId = session.get('userId', None)
    
    # Bad info, but they've disconnected anyways...
    if None in (tourneyId, userId):
        return
    
    user = brawlapi.getUser(tourneyId, userId)
    
    # User doesn't exist
    if user is None:
        return
    
    brawlapi.removeOnlineUser(tourneyId, user)

    print('User {} disconnected'.format(user.userId))

# A participant win was reported
@socketio.on('report win', namespace='/participant')
def participant_report_win(data):
    participantId = data['player-id']
    tourneyId = session['tourneyId']
    matchId = brawlapi.getParticipantMatch(tourneyId, participantId)
    
    print('Participant #{} won a game. mID: {}, tId: {}'
        .format(participantId, matchId, tourneyId))
    
    brawlapi.incrementMatchScore(tourneyId, matchId, (1, 0))
    
    lData = brawlapi.getLobbyData(tourneyId, matchId)
    emit('update lobby', lData,
        broadcast=True, include_self=True, room=matchId)
    
# A player updated their settings
@socketio.on('update settings', namespace='/participant')
def participant_update_settings(settings):
    userId = session['userId']
    tourneyId = session['tourneyId']
    
    # Weren't passed a userId
    if userId is None:
        print('User id missing; connection rejected')
        emit('error', {'code': 'bad-participant'},
            broadcast=False, include_self=True)
        return False
    
    user = brawlapi.getUser(tourneyId, userId)
    
    if user.setSettings(settings):
        emit('update settings', settings,
             broadcast=False, include_self=True)
    else:
        emit('invalid settings')

# A chat message was sent by a client
@socketio.on('send', namespace='/chat')
def chat_send(data):
    tourneyId = session.get('tourneyId', None)
    userId = session.get('userId', None)
    
    # No tourneyId, userId. Could probably be handled more gracefully
    if None in (tourneyId, userId):
        print('Tried to send chat message with bad info. tId: {}, uId: {}'
            .format(tourneyId, userId))
        return
    
    user = brawlapi.getUser(tourneyId, userId)
    
    # User doesn't exist
    if user is None:
        print('User doesn\'t exist; connection rejected')
        emit('error', {'code': 'bad-participant'},
            broadcast=False, include_self=True)
        return False
        
    sentTime = datetime.datetime.now().isoformat()
    
    chatId = data['chatId']
    message = data['message']
    
    chat = brawlapi.getChat(tourneyId, chatId)
    if not chat:
        return
        
    room = chat.getRoom()
    
    # User not in this chat
    if room not in rooms():
        return
    
    pData = brawlapi.getParticipantData(tourneyId, user.participantId)
    # This should really never happen, it should have been guaranteed by
    # them connecting
    if pData is None:
        print('Couldn\'t find pData while sending chat. tID: {}, pID: {}'
            .format(tourneyId, user.participantId))
        return
    
    avatarURL = brawlapi.getParticipantAvatar(pData)
    
    messageData = {'senderId': str(user.userId),
                   'avatar': avatarURL,
                   'name': pData['name'],
                   'message': message,
                   'sentTime': sentTime}
    
    chat.addMessage(messageData)
    
    emit('receive', {
        'messageData': messageData,
        'chatId': chatId
    }, broadcast=True, include_self=True, room=room)
    
# A user is requesting a full chat log
@socketio.on('request log', namespace='/chat')
def chat_request_log(data):
    tourneyId = session['tourneyId']
    sentTime = datetime.datetime.now().isoformat()
    
    chatId = data['chatId']
    
    chat = brawlapi.getChat(tourneyId, chatId)
    if not chat:
        return
        
    room = chat.getRoom()
    
    # User not in this chat
    if room not in rooms():
        return
    
    emit('receive log', {
        'log': chat.log,
        'chatId': chatId
    }, broadcast=False, include_self=True)
        
if __name__ == '__main__':
    app.debug = True
    socketio.run(app)