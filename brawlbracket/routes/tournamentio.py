from functools import wraps

from flask import session
from flask import request
from flask import g
from flask import abort
from flask_socketio import join_room
from flask_socketio import leave_room
from flask_socketio import emit

from brawlbracket.app import socketio
from brawlbracket import usermanager as um
from brawlbracket import tournamentmanager as tm

print('Registering tournamentio routes...')

def require_tourney_data(f):
    """
    Place all the data needed for tournament namespace socketIO calls in g. The following will be set:
    g.userId
    g.user
    g.tourneyId
    g.tournament
    g.match
    g.team
    g.player
    
    An error will be emitted if any of the above values are invalid.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        g.userId = session.get('userId', None)
        g.user = um.getUserById(g.userId)
        
        # User doesn't exist
        if g.user is None:
            print('User doesn\'t exist; connection rejected')
            emit('error', {'code': 'bad-participant'},
                broadcast=False, include_self=True)
            return False
            
        g.tourneyId = session.get('tourneyId', None)
        g.tournament = tm.getTournamentById(g.tourneyId)
            
        if g.tournament is None:
            # TODO: add actual error message
            abort(404)
            
        info = g.tournament.getUserInfo(g.user)
        
        # User isn't in this tournament
        if info is None:
            # TODO: add actual error message
            abort(403)
            
        g.match, g.team, g.player = info
            
        return f(*args, **kwargs)
        
    return decorated_function

@socketio.on('connect', namespace='/tournament')
@require_tourney_data
def user_connect():
    # Extra data that we'll send in the handshake event
    extraData = {
        'playerSettings': g.user.getSettings()
    }
    
    if g.team.eliminated:
        # This can be handled more gracefully
        abort(404)
    
    # Affect match state
    g.player.online += 1
    
    # XXX update state, put in listener
    g.match._updateState()
    
    # Join new room
    session['matchId'] = g.match.id
    join_room(g.match.id)

    # This needs to be done in the /chat namespace, so switch it temporarily
    request.namespace = '/chat'
    join_room(g.match.chat.getRoom())
    if g.player.adminChat:
        join_room(g.player.adminChat.getRoom())
    request.namespace = '/tournament'
    
    extraData['adminChat'] = str(g.player.adminChat.id if g.player.adminChat else None)
    
    print('Participant {} connected, joined room #{}'
        .format(g.user.id, g.match.id))
    
    lobbyData = g.match.lobbyData
    
    # Admin-only data
    if g.tournament.isAdmin(g.user):
        extraData['playerChats'] = [ str(p.adminChat.id) for p in g.tournament.players ]
        
        # This needs to be done in the /chat namespace, so switch it temporarily
        # Join all players' admin chats
        request.namespace = '/chat'
        for p in g.tournament.players:
            if p.adminChat:
                join_room(p.adminChat.getRoom())
        request.namespace = '/tournament'
    
    emit('handshake', extraData,
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
            room = g.match.id, namespace='/tournament')
    
@socketio.on('disconnect', namespace='/tournament')
@require_tourney_data
def user_disconnect():
    # Affect state
    g.player.online -= 1
    
    if g.match is not None:
        # XXX update state, put in listener
        g.match._updateState()
    # Match is none, player was eliminated
    else:
        return
    
    lobbyData = g.match.lobbyData
    updatedLobbyData = {}
    updatedLobbyData['teams'] = lobbyData['teams']
    updatedLobbyData['state'] = lobbyData['state']
    
    emit('update lobby', updatedLobbyData, broadcast=True, include_self=False,
            room = g.match.id)
    
    print('User {} disconnected'.format(g.user.id))
    
# State reporting from client

# Someone picked their legend
@socketio.on('pick legend', namespace='/tournament')
@require_tourney_data
def pick_legend(data):
    g.player.currentLegend = data['legendId']
    g.match._updateState()
    
    lobbyData = g.match.lobbyData
    updatedLobbyData = {}
    updatedLobbyData['state'] = lobbyData['state']
    updatedLobbyData['teams'] = lobbyData['teams']
    
    emit('update lobby', updatedLobbyData, broadcast=True, include_self=True,
            room = g.match.id)
    
    print('User {} selected {}'.format(g.user.id, data['legendId']))
    
# Someone banned a realm
@socketio.on('ban realm', namespace='/tournament')
@require_tourney_data
def ban_realm(data):
    g.match.addRealmBan(data['realmId'])
    g.match._updateState()
    
    lobbyData = g.match.lobbyData
    updatedLobbyData = {}
    updatedLobbyData['state'] = lobbyData['state']
    updatedLobbyData['realmBans'] = lobbyData['realmBans']
    updatedLobbyData['currentRealm'] = lobbyData['currentRealm']
    
    emit('update lobby', updatedLobbyData, broadcast=True, include_self=True,
            room = g.match.id)
    print('Banned {}'.format(data['realmId']))
    
# Someone picked a realm
@socketio.on('pick realm', namespace='/tournament')
@require_tourney_data
def pick_realm(data):
    g.match.currentRealm = data['realmId']
    g.match._updateState()
    
    lobbyData = g.match.lobbyData
    updatedLobbyData = {}
    updatedLobbyData['state'] = lobbyData['state']
    updatedLobbyData['currentRealm'] = lobbyData['currentRealm']
    
    emit('update lobby', updatedLobbyData, broadcast=True, include_self=True,
            room = g.match.id)
    print('Picked {}'.format(data['realmId']))

# A room was selected
@socketio.on('set room', namespace='/tournament')
@require_tourney_data
def select_room(data):
    g.match.roomNumber = data['roomNumber']
    g.match._updateState()
    
    lobbyData = g.match.lobbyData
    updatedLobbyData = {}
    updatedLobbyData['state'] = lobbyData['state']
    updatedLobbyData['roomNumber'] = lobbyData['roomNumber']
    
    emit('update lobby', updatedLobbyData, broadcast=True, include_self=True,
            room = g.match.id)
    print('Selected room number {}'.format(data['roomNumber']))
    
    
# A team win was reported
@socketio.on('report win', namespace='/tournament')
@require_tourney_data
def report_win(data):
    g.match.incrementScore(data['teamIndex'])
    
    g.match._updateState()
    
    lobbyData = g.match.lobbyData
    updatedLobbyData = {}
    updatedLobbyData['state'] = lobbyData['state']
    updatedLobbyData['teams'] = lobbyData['teams']
    updatedLobbyData['currentRealm'] = lobbyData['currentRealm']
    updatedLobbyData['realmBans'] = lobbyData['realmBans']
    
    emit('update lobby', updatedLobbyData, broadcast=True, include_self=True,
            room = g.match.id)
    
    if g.match.winner is not None and g.match.nextMatch is not None:
        nextLobbyData = g.match.nextMatch.lobbyData
        updatedNextLobbyData = {}
        updatedNextLobbyData['state'] = nextLobbyData['state']
        updatedNextLobbyData['teams'] = nextLobbyData['teams']
        emit('update lobby', updatedNextLobbyData, broadcast=True, 
                include_self=False, room = g.match.nextMatch.id)

# A player is ready to advance to the next match
@socketio.on('advance lobby', namespace='/tournament')
@require_tourney_data
def advance_lobby():
    if g.team.eliminated:
        raise AssertionError('Eliminated player trying to advance match.')
    
    for m in g.match.prereqMatches:
        if m is None:
            continue
        for t in m.teams:
            # This user's team in a previous match, we want to leave rooms
            # associated with this match
            if t.id == g.team.id:
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
    join_room(g.match.id)
    
    # This needs to be done in the /chat namespace, so switch it temporarily
    request.namespace = '/chat'
    join_room(g.match.chat.getRoom())
    request.namespace = '/tournament'
    
    emit('join lobby', {'lobbyData': g.match.lobbyData},
            broadcast=False, include_self=True, room = g.match.id)