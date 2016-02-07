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

import os
import datetime
import brawlapi

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

#----- User pages -----#

# User app page
@app.route('/<tourneyName>/app/')
def user_landing(tourneyName):
    tourneyId = session['tourneyId']
    participantId = session['participantId']
    
    pData = brawlapi.getParticipantData(tourneyId, participantId)

    return render_template('user-app.html',
                           userName=pData['display-name'],
                           userAvatar=brawlapi.getParticipantAvatar(pData),
                           tourneyName=tourneyName,
                           tourneyFullName=brawlapi.getTournamentName(tourneyName),
                           participantId=participantId)

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
    return render_template('app-content/player-settings.html',
                           tourneyFullName=brawlapi.getTournamentName(tourneyName),
                           tourneyName=tourneyName,
                           participantId=session['participantId'],
                           legendData=brawlapi.orderedLegends,
                           serverRegions=list(brawlapi.serverRegions.items()))
    
# Lobby content
@app.route('/app-content/lobby/<tourneyName>')
def lobby(tourneyName):
    return render_template('app-content/lobby.html',
                           tourneyFullName=brawlapi.getTournamentName(tourneyName))

#----- Page elements -----#
    
# Connect error
@app.route('/app-content/lobby-error/<tourneyName>')
def lobby_error(tourneyName):
    return render_template('app-content/lobby-error.html')
    
# Legend roster
@app.route('/app-content/roster')
def roster():
    return render_template('app-content/lobby-roster.html',
    legendData=brawlapi.orderedLegends)
    
# Map picker
@app.route('/app-content/realms')
def realms():
    return render_template('app-content/lobby-realms.html',
                           realmData=brawlapi.orderedRealms)

    
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
    
    # Find current match, this is and INT
    matchId = brawlapi.getParticipantMatch(tId, pId)
        
    # Handle no match found
    if matchId is None:
        print('Participant #{} connected but found no match.'.format(pId))
        emit('error', {'code': 'no-match'},
            broadcast=False, include_self=True)
        return False
    
    # Join new room
    session['matchId'] = matchId
    join_room(matchId)
    
    print('Participant #{} connected, joined room #{}'
        .format(pId, matchId))
        
    lobbyData = brawlapi.getLobbyData(tId, matchId)
    playerSettings = brawlapi.getPlayerSettings(tId, pId)
    
    # Join chat room
    if lobbyData['chatId'] == None:
        chatId = brawlapi.createChat(tId)
        lobbyData['chatId'] = chatId
        
    chat = brawlapi.getChat(tId, lobbyData['chatId'])
    join_room(chat.getRoom())
        
    emit('join lobby', {
            'lobbyData': lobbyData,
            'playerSettings': playerSettings
        },
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
    participantId = data['player-id']
    tourneyId = session['tourneyId']
    matchId = brawlapi.getParticipantMatch(tourneyId, participantId)
    
    print('Participant #{} won a game. mID: {}, tId: {}'
        .format(participantId, matchId, tourneyId))
    
    brawlapi.incrementMatchScore(tourneyId, matchId, (1, 0))
    
    lData = brawlapi.getLobbyData(tourneyId, matchId)
    emit('update lobby', lData,
        broadcast=True, include_self=True, room=matchId)

# A chat message was sent by a client
@socketio.on('send chat', namespace='/participant')
def participant_chat(data):
    tourneyId = session['tourneyId']
    participantId = session['participantId']
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
    
    pData = brawlapi.getParticipantData(tourneyId, participantId)
    # This should really never happen, it should have been guaranteed by
    # them connecting
    if pData is None:
        print('Couldn\'t find pData while sending chat. pID: {}, tID: {}'
            .format(participantId, tourneyId))
        return
    
    avatarURL = brawlapi.getParticipantAvatar(pData)
    
    messageData = {'senderId': participantId,
                   'avatar': avatarURL,
                   'name': pData['name'],
                   'message': message,
                   'sentTime': sentTime}
    
    chat.addMessage(messageData)
    
    emit('receive chat', {
        'messageData': messageData,
        'chatId': chatId
    }, broadcast=True, include_self=True, room=room)
    
# A user is requesting a full chat log
@socketio.on('request chat log', namespace='/participant')
def participant_request_chat_log(data):
    tourneyId = session['tourneyId']
    participantId = session['participantId']
    sentTime = datetime.datetime.now().isoformat()
    
    chatId = data['chatId']
    
    chat = brawlapi.getChat(tourneyId, chatId)
    if not chat:
        return
        
    room = chat.getRoom()
    
    # User not in this chat
    if room not in rooms():
        return
    
    emit('chat log', {
        'log': chat.log,
        'chatId': chatId
    }, broadcast=False, include_self=True, room=room)

# A player updated their settings
@socketio.on('update settings', namespace='/participant')
def participant_update_settings(settings):
    participantId = session['participantId']
    tourneyId = session['tourneyId']
    
    if brawlapi.setPlayerSettings(tourneyId, participantId, settings):
        emit('update settings', settings,
             broadcast=False, include_self=True)
    else:
        emit('invalid settings')
        
if __name__ == '__main__':
    app.debug = True
    socketio.run(app)