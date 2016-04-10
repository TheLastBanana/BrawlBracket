from flask import session
from flask import request
from flask_socketio import join_room
from flask_socketio import leave_room
from flask_socketio import emit

from brawlbracket.app import socketio
from brawlbracket import usermanager as um
from brawlbracket import tournamentmanager as tm

print('Registering tournamentio routes...')

@socketio.on('connect', namespace='/tournament')
def user_connect():
    userId = session.get('userId', None)
    user = um.getUserById(userId)
    tourneyId = session.get('tourneyId', None)
    tournament = tm.getTournamentById(tourneyId)
    
    # User doesn't exist
    if user is None:
        print('User doesn\'t exist; connection rejected')
        emit('error', {'code': 'bad-participant'},
            broadcast=False, include_self=True)
        return False
    
    #Tournament doesn't exist
    if tournament is None:
        abort(404)
    
    info = tournament.getUserInfo(user)
    
    if info is None:
        # TODO: Issue error saying we somehow got into a tournament that
        # we don't live in
        pass
    
    match, team, player = info
    
    if team.eliminated:
        # This can be handled more gracefully
        abort(404)
    
    # Affect match state
    player.online += 1
    
    # XXX update state, put in listener
    match._updateState()
    
    # Join new room
    session['matchId'] = match.id
    join_room(match.id)
    
    print('Participant {} connected, joined room #{}'
        .format(user.id, match.id))
    
    # This needs to be done in the /chat namespace, so switch it temporarily
    request.namespace = '/chat'
    join_room(match.chat.getRoom())
    request.namespace = '/tournament'
    
    lobbyData = match.lobbyData
    # Extra data since we can't send things in the connect event
    emit('handshake', {
            'playerSettings': user.getSettings()
        },
        broadcast=False, include_self=True)
        
    # Tell the user to join their first match too
    emit('join lobby', {
            'lobbyData': lobbyData
        },
        broadcast=False, include_self=True)
        
    # TODO: update match state and post lobby updates to room 
    updatedLobbyData = {}
    updatedLobbyData['teams'] = lobbyData['teams']
    updatedLobbyData['state'] = lobbyData['state']
    
    emit('update lobby', updatedLobbyData, broadcast=True, include_self=False,
            room = match.id, namespace='/tournament')
    
@socketio.on('disconnect', namespace='/tournament')
def user_disconnect():
    userId = session.get('userId', None)
    tournamentId = session.get('tourneyId', None)
    
    user = um.getUserById(userId)
    
    # User doesn't exist, this shouldn't happen ever
    if user is None:
        raise AssertionError('User disconnected, but didn\'t exist')
        
    tournament = tm.getTournamentById(tournamentId)
    if tournament is None:
        abort(404)
    
    # Tournament doesn't exist
    if tournament is None:
        return
    
    info = tournament.getUserInfo(user)
    
    if info is None:
        # TODO: Issue error saying we somehow got into a tournament that
        # we don't live in
        pass
    
    match, team, player = info
    
    # Affect state
    player.online -= 1
    
    if match is not None:
        # XXX update state, put in listener
        match._updateState()
    # Match is none, player was eliminated
    else:
        return
    
    lobbyData = match.lobbyData
    updatedLobbyData = {}
    updatedLobbyData['teams'] = lobbyData['teams']
    updatedLobbyData['state'] = lobbyData['state']
    
    emit('update lobby', updatedLobbyData, broadcast=True, include_self=False,
            room = match.id)
    
    print('User {} disconnected'.format(user.id))
    
# State reporting from client

# Someone picked their legend
@socketio.on('pick legend', namespace='/tournament')
def pick_legend(data):
    userId = session.get('userId', None)
    user = um.getUserById(userId)
    tourneyId = session.get('tourneyId', None)
    tournament = tm.getTournamentById(tourneyId)
    
    # User doesn't exist
    if user is None:
        print('User doesn\'t exist; connection rejected')
        emit('error', {'code': 'bad-participant'},
            broadcast=False, include_self=True)
        return False
    
    #Tournament doesn't exist
    if tournament is None:
        abort(404)
    
    info = tournament.getUserInfo(user)
    
    if info is None:
        # TODO: Issue error saying we somehow got into a tournament that
        # we don't live in
        pass
    
    match, team, player = info
    
    player.currentLegend = data['legendId']
    match._updateState()
    
    lobbyData = match.lobbyData
    updatedLobbyData = {}
    updatedLobbyData['state'] = lobbyData['state']
    updatedLobbyData['teams'] = lobbyData['teams']
    
    emit('update lobby', updatedLobbyData, broadcast=True, include_self=True,
            room = match.id)
    
    print('User {} selected {}'.format(user.id, data['legendId']))
    
# Someone banned a realm
@socketio.on('ban realm', namespace='/tournament')
def ban_realm(data):
    userId = session.get('userId', None)
    user = um.getUserById(userId)
    tourneyId = session.get('tourneyId', None)
    tournament = tm.getTournamentById(tourneyId)
    
    # User doesn't exist
    if user is None:
        print('User doesn\'t exist; connection rejected')
        emit('error', {'code': 'bad-participant'},
            broadcast=False, include_self=True)
        return False
    
    #Tournament doesn't exist
    if tournament is None:
        abort(404)
    
    info = tournament.getUserInfo(user)
    
    if info is None:
        # TODO: Issue error saying we somehow got into a tournament that
        # we don't live in
        pass
    
    match, team, player = info
    
    match.addRealmBan(data['realmId'])
    match._updateState()
    
    lobbyData = match.lobbyData
    updatedLobbyData = {}
    updatedLobbyData['state'] = lobbyData['state']
    updatedLobbyData['realmBans'] = lobbyData['realmBans']
    updatedLobbyData['currentRealm'] = lobbyData['currentRealm']
    
    emit('update lobby', updatedLobbyData, broadcast=True, include_self=True,
            room = match.id)
    print('Banned {}'.format(data['realmId']))
    
# Someone picked a realm
@socketio.on('pick realm', namespace='/tournament')
def pick_realm(data):
    userId = session.get('userId', None)
    user = um.getUserById(userId)
    tourneyId = session.get('tourneyId', None)
    tournament = tm.getTournamentById(tourneyId)
    
    # User doesn't exist
    if user is None:
        print('User doesn\'t exist; connection rejected')
        emit('error', {'code': 'bad-participant'},
            broadcast=False, include_self=True)
        return False
    
    #Tournament doesn't exist
    if tournament is None:
        abort(404)
    
    info = tournament.getUserInfo(user)
    
    if info is None:
        # TODO: Issue error saying we somehow got into a tournament that
        # we don't live in
        pass
    
    match, team, player = info
    
    match.currentRealm = data['realmId']
    match._updateState()
    
    lobbyData = match.lobbyData
    updatedLobbyData = {}
    updatedLobbyData['state'] = lobbyData['state']
    updatedLobbyData['currentRealm'] = lobbyData['currentRealm']
    
    emit('update lobby', updatedLobbyData, broadcast=True, include_self=True,
            room = match.id)
    print('Picked {}'.format(data['realmId']))

# A room was selected
@socketio.on('set room', namespace='/tournament')
def select_room(data):
    userId = session.get('userId', None)
    user = um.getUserById(userId)
    tourneyId = session.get('tourneyId', None)
    tournament = tm.getTournamentById(tourneyId)
    
    # User doesn't exist
    if user is None:
        print('User doesn\'t exist; connection rejected')
        emit('error', {'code': 'bad-participant'},
            broadcast=False, include_self=True)
        return False
    
    #Tournament doesn't exist
    if tournament is None:
        abort(404)
    
    info = tournament.getUserInfo(user)
    
    if info is None:
        # TODO: Issue error saying we somehow got into a tournament that
        # we don't live in
        pass
    
    match, team, player = info
    
    match.roomNumber = data['roomNumber']
    match._updateState()
    
    lobbyData = match.lobbyData
    updatedLobbyData = {}
    updatedLobbyData['state'] = lobbyData['state']
    updatedLobbyData['roomNumber'] = lobbyData['roomNumber']
    
    emit('update lobby', updatedLobbyData, broadcast=True, include_self=True,
            room = match.id)
    print('Selected room number {}'.format(data['roomNumber']))
    
    
# A team win was reported
@socketio.on('report win', namespace='/tournament')
def report_win(data):
    userId = session.get('userId', None)
    user = um.getUserById(userId)
    tourneyId = session.get('tourneyId', None)
    tournament = tm.getTournamentById(tourneyId)
    
    # User doesn't exist
    if user is None:
        print('User doesn\'t exist; connection rejected')
        emit('error', {'code': 'bad-participant'},
            broadcast=False, include_self=True)
        return False
    
    #Tournament doesn't exist
    if tournament is None:
        abort(404)
    
    info = tournament.getUserInfo(user)
    
    if info is None:
        # TODO: Issue error saying we somehow got into a tournament that
        # we don't live in
        pass
    
    match, team, player = info
    
    match.incrementScore(data['teamIndex'])
    
    match._updateState()
    
    lobbyData = match.lobbyData
    updatedLobbyData = {}
    updatedLobbyData['state'] = lobbyData['state']
    updatedLobbyData['teams'] = lobbyData['teams']
    updatedLobbyData['currentRealm'] = lobbyData['currentRealm']
    updatedLobbyData['realmBans'] = lobbyData['realmBans']
    
    emit('update lobby', updatedLobbyData, broadcast=True, include_self=True,
            room = match.id)
    
    if match.winner is not None and match.nextMatch is not None:
        nextLobbyData = match.nextMatch.lobbyData
        updatedNextLobbyData = {}
        updatedNextLobbyData['state'] = nextLobbyData['state']
        updatedNextLobbyData['teams'] = nextLobbyData['teams']
        emit('update lobby', updatedNextLobbyData, broadcast=True, 
                include_self=False, room = match.nextMatch.id)

# A player is ready to advance to the next match
@socketio.on('advance lobby', namespace='/tournament')
def advance_lobby():
    userId = session.get('userId', None)
    user = um.getUserById(userId)
    tourneyId = session.get('tourneyId', None)
    tournament = tm.getTournamentById(tourneyId)
    
    # User doesn't exist
    if user is None:
        print('User doesn\'t exist; connection rejected')
        emit('error', {'code': 'bad-participant'},
            broadcast=False, include_self=True)
        return False
    
    #Tournament doesn't exist
    if tournament is None:
        abort(404)
    
    info = tournament.getUserInfo(user)
    
    if info is None:
        # TODO: Issue error saying we somehow got into a tournament that
        # we don't live in
        pass
    
    match, team, player = info
    
    if team.eliminated:
        raise AssertionError('Eliminated player trying to advance match.')
    
    for m in match.prereqMatches:
        if m is None:
            continue
        for t in m.teams:
            # This user's team in a previous match, we want to leave rooms
            # associated with this match
            if t.id == team.id:
                leave_room(m.id)
                
                # This needs to be done in the /chat namespace, so switch it temporarily
                request.namespace = '/chat'
                leave_room(m.chat.getRoom())
                request.namespace = '/tournament'
                
                break
        # Continue if we didn't find it
        else:
            continue
        # Break because we found it
        break
    else:
        raise AssertionError('Didn\'t find rooms to leave.')
    
    # Join new match lobby
    join_room(match.id)
    
    # This needs to be done in the /chat namespace, so switch it temporarily
    request.namespace = '/chat'
    join_room(match.chat.getRoom())
    request.namespace = '/tournament'
    
    emit('join lobby', {'lobbyData': match.lobbyData},
            broadcast=False, include_self=True, room = match.id)