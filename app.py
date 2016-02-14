from collections import namedtuple
import uuid
import os
import datetime

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
from bidict import bidict

import brawlapi
import util

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
        
        userList = brawlapi.getTournamentUsersOverview(tourneyId)

        return render_template('user-login.html',
                               tourneyName=prettyName,
                               participants=userList,
                               challongeURL=tourneyURL)
   
    # POST was used
    # TODO: validate user ID
    userIdStr = request.form['user']
    session['userId'] = uuid.UUID(userIdStr)
    session['tourneyId'] = tourneyId
    
    return redirect(url_for('user_landing', tourneyName=tourneyName))

#----- User pages -----#

# User app page
@app.route('/<tourneyName>/app/', defaults={'startPage': None})
@app.route('/<tourneyName>/app/<startPage>/')
def user_landing(tourneyName, startPage):
    tourneyId = session.get('tourneyId', None)
    userId = session.get('userId', None)
    
    if None in (tourneyId, userId):
        print('No tourneyId or userId; returned to login.')
        return redirect(url_for("user_login", tourneyName=tourneyName))
        
    user = brawlapi.getUser(tourneyId, userId)
    
    if user is None:
        print('User doesn\'t exist; returned to login.')
        return redirect(url_for("user_login", tourneyName=tourneyName))
    
    # Shouldn't need to check for None, this should come guaranteed with
    # finding a user
    pData = brawlapi.getParticipantData(tourneyId, user.participantId)

    return render_template('user-app.html',
                           startPage=startPage,
                           userName=pData['display-name'],
                           userAvatar=brawlapi.getParticipantAvatar(pData),
                           tourneyName=tourneyName,
                           tourneyFullName=brawlapi.getTournamentName(tourneyName),
                           userId=user.userId,
                           basePath='/{}/app/'.format(tourneyName))

# Contact admin page
@app.route('/app-content/contact-admin/<tourneyName>')
def contact_admin(tourneyName):
    return render_template('app-content/contact-admin.html',
                           tourneyFullName=brawlapi.getTournamentName(tourneyName))
    
# Bracket viewer page
@app.route('/app-content/bracket/<tourneyName>')
def bracket(tourneyName):
    tourneyId = tourneys[tourneyName]

    return render_template('app-content/bracket.html',
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
        
    return render_template('app-content/player-settings.html',
                           tourneyFullName=brawlapi.getTournamentName(tourneyName),
                           tourneyName=tourneyName,
                           participantId=session['userId'],
                           legendData=util.orderedLegends,
                           serverRegions=list(util.serverRegions.items()))
    
# Lobby content
@app.route('/app-content/lobby/<tourneyName>')
def lobby(tourneyName):
    return render_template('app-content/lobby.html',
                           tourneyFullName=brawlapi.getTournamentName(tourneyName))

#----- Admin pages -----#
                           
# Admin app page
@app.route('/<tourneyName>/admin/<adminKey>/', defaults={'startPage': None})
@app.route('/<tourneyName>/admin/<adminKey>/<startPage>/')
def admin_landing(tourneyName, adminKey, startPage):
    tourneyId = tourneys[tourneyName]
    tourneyKeys = brawlapi.adminKeys[tourneyId]
    
    session['adminMode'] = True
    session['participantId'] = -1
    
    # If the key is wrong, don't let the user log in
    if adminKey not in tourneyKeys:
        abort(404)

    return render_template('admin-app.html',
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
        
    # Get a condensed list of lobby data for display to the admin
    lobbies = []
    
    DashLobbyData = namedtuple('DashLobbyData', [
        'id',
        'p1Name',
        'p2Name',
        'score',
        'room',
        'status',
        'prettyStatus',
        'statusOrder'
    ])
    
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
        
        dashLobbyData = DashLobbyData(
            id = lobbyData['challongeId'],
            p1Name = participants[0]['name'] if len(participants) > 0 else '',
            p2Name = participants[1]['name'] if len(participants) > 1 else '',
            score = scoreString,
            room = lobbyData['roomNumber'] or '',
            status = lobbyData['state']['name'],
            prettyStatus = prettyStatus,
            statusOrder = statusOrder)
        
        lobbies.append(dashLobbyData)
        
        
    # Get a condensed list of user data for display to the admin
    dashUserDatas = []
    
    DashUserData = namedtuple('DashUserData', [
        'seed',
        'name',
        'prettyStatus',
        'status',
        'online'
    ])
    
    users = brawlapi.getTournamentUsers(tourneyId)
    for user in users:
        status, prettyStatus = brawlapi.getParticipantStatus(tourneyId, user)
        pData = brawlapi.getParticipantData(tourneyId, user.participantId)
        
        online = 'Offline'
        if brawlapi.isUserOnline(tourneyId, user):
            online = 'Online'
    
        dashUserData = DashUserData(
            seed = pData['seed'],
            name = pData['display-name'],
            status = status,
            prettyStatus = prettyStatus,
            online = online)
        
        dashUserDatas.append(dashUserData)

    return render_template('app-content/admin-dashboard.html',
                           liveImageURL=brawlapi.getTournamentLiveImageURL(tourneyId),
                           tourneyFullName=brawlapi.getTournamentName(tourneyName),
                           lobbies=lobbies,
                           users=dashUserDatas)
    
#----- Page elements -----#
    
# Connect error
@app.route('/app-content/lobby-error/<tourneyName>')
def lobby_error(tourneyName):
    return render_template('app-content/lobby-error.html')
    
# Legend roster
@app.route('/app-content/roster')
def roster():
    return render_template('app-content/lobby-roster.html',
    legendData=util.orderedLegends)
    
# Map picker
@app.route('/app-content/realms')
def realms():
    return render_template('app-content/lobby-realms.html',
                           realmData=util.orderedRealms)

    
#----- SocketIO events -----#
@socketio.on('connect', namespace='/participant')
def participant_connect():
    userId = session.get('userId', None)
    tourneyId = session.get('tourneyId', None)
    
    # Weren't passed a userId
    if userId is None:
        print('User id missing; connection rejected')
        emit('error', {'code': 'bad-participant'},
            broadcast=False, include_self=True)
        return False
    
    user = brawlapi.getUser(tourneyId, userId)
    
    # User doesn't exist
    if user is None:
        print('User doesn\'t exist; connection rejected')
        emit('error', {'code': 'bad-participant'},
            broadcast=False, include_self=True)
        return False
    
    if brawlapi.isUserOnline(tourneyId, user):
        print('User {} rejected (already connected)'
            .format(user.userId))
        emit('error', {'code': 'already-connected'},
            broadcast=False, include_self=True)
        return False
    
    brawlapi.addOnlineUser(tourneyId, user)
    
    # Find current match
    matchId = brawlapi.getParticipantMatch(tourneyId, user)
        
    # Handle no match found
    if matchId is None:
        print('User {} connected but found no match.'.format(user.userId))
        emit('error', {'code': 'no-match'},
            broadcast=False, include_self=True)
        return False
    
    # Join new room
    session['matchId'] = matchId
    join_room(matchId)
    
    print(request.sid)
    
    print('Participant {} connected, joined room #{}'
        .format(user.userId, matchId))
        
    lobbyData = brawlapi.getLobbyData(tourneyId, matchId)
    
    # Join chat room
    if lobbyData['chatId'] == None:
        chatId = brawlapi.createChat(tourneyId)
        lobbyData['chatId'] = chatId
    
    # This needs to be done in the /chat namespace, so switch it temporarily
    chat = brawlapi.getChat(tourneyId, lobbyData['chatId'])
    request.namespace = '/chat'
    join_room(chat.getRoom())
    request.namespace = '/participant'
        
    emit('join lobby', {
            'lobbyData': lobbyData,
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
    }, broadcast=False, include_self=True, room=room)
        
if __name__ == '__main__':
    app.debug = True
    socketio.run(app)