import os
import datetime
from urllib.error import HTTPError

import challonge

import db_wrapper

# Set up challonge
challonge.set_credentials(os.environ.get('BB_CHALLONGE_USER'), os.environ.get('BB_CHALLONGE_API_KEY'))

# Cached Challonge data
tourneyDatas = {}
matchDatas = {}
participantDatas = {}
lobbyDatas = {}

# Set of online participant IDs
onlineUsers = set()

# +------------------+
# | Helper Functions |
# +------------------+

def matchIdToNumber(matchId):
    """
    Convert a match's letter identifier to numbers.
    """
    idSum = 0
    
    for letter in matchId:
        value = ord(letter.upper()) - 64
        
        if value < 1 or value > 26:
            raise ValueError("Match identifier should only contain letters (got '{}')".format(letter))
    
        # A = 65, but we want A = 1
        idSum += value
        
    return idSum

# +---------------+
# | User Managing |
# +---------------+
# Much int paranoia

def addOnlineUser(participantId):
    """
    Track user as online.
    """
    onlineUsers.add(int(participantId))

def removeOnlineUser(participantId):
    """
    Stop tracking user as online.
    """
    onlineUsers.remove(int(participantId))

def isUserOnline(participantId):
    """
    Determine if a user is online.
    
    Return False if user is None.
    Return True if user is online.
    Return False if user is not online.
    """
    if participantId is None:
        return False
        
    return int(participantId) in onlineUsers
    
# +------------------------+
# | Refresh data functions |
# +------------------------+
# TODO: Add database functionality to all of these rather than just caching


def refreshTournamentData(tourneyId):
    """
    Refreshes the tournament data for tourneyId.
    
    No return.
    
    TODO: Make sure this is called reasonably often.
    """
    tourneyData = challonge.tournaments.show(tourneyId)
    tourneyDatas[tourneyId] = tourneyData
        
def refreshMatchIndex(tourneyId):
    """
    Refreshes the match data for tourneyId.
    
    No return.
    
    TODO: Make sure this is called reasonably often.
    """
    try:
        tourneyData = {}
        mIndex = challonge.matches.index(tourneyId)
        
        for mData in mIndex:
            tourneyData[mData['id']] = mData
            
        matchDatas[tourneyId] = tourneyData

    except HTTPError as e:
        print('Got {} - \"{}\" while refreshing match index. tID:{}.'
            .format(e.code, e.reason, tourneyId))
            
def refreshMatchData(tourneyId, matchId):
    """
    Refreshes data for a specific match in a tournament.
    If the tournament isn't cached then the index will be refreshed.
    
    No return.
    """
    # If we don't have the tourney, try and get it
    if tourneyId not in matchDatas:
        refreshMatchIndex(tourneyId)
        
        # We tried our best to get the match, it's up to calling code 
        # to discover if it's not there
        return
        
    # Refresh match
    try:
        mData = challonge.matches.show(tourneyId, matchId)
        matchDatas[tourneyId][matchId] = mData
    except HTTPError as e:
        print('Got {} - \"{}\" while showing match tID:{}, mID{}.'
            .format(e.code, e.reason, tourneyId, matchId))
    
def refreshParticipantIndex(tourneyId):
    """
    Refreshes the participant data for tourneyId.
    
    No return.
    
    Todo: Make sure this is called reasonably often.
    """
    try:
        tourneyData = {}
        pIndex = challonge.participants.index(tourneyId)
        
        for pData in pIndex:
            # Convert to int
            tourneyData[int(pData['id'])] = pData
            
        participantDatas[tourneyId] = tourneyData
    
    except HTTPError as e:
        print('Got {} - \"{}\" while refreshing participant index. tID:{}.'
            .format(e.code, e.reason, tourneyId))

def refreshParticipantData(tourneyId, participantId):
    """
    Refreshes data for a specific participant in a tournament.
    If the tournament isn't cached then the index will be refreshed.
    
    No return.
    """
    # If we don't have the tourney, try and get it
    if tourneyId not in participantDatas:
        refreshParticipantIndex(tourneyId)
        
        # We tried our best to get the participant, it's up to calling code 
        # to discover if it's not there
        return
        
    # Refresh participant
    try:
        pData = challonge.participants.show(tourneyId, participantId)
        participantDatas[tourneyId][participantId] = pData
    except HTTPError as e:
        print('Got {} - \"{}\" while showing participant tID:{}, pID{}.'
            .format(e.code, e.reason, tourneyId, participantId))
    
   
# +--------------------+
# | Get data functions |
# +--------------------+

def getTournamentName(tourneyId):
    """
    Get a tournament's "pretty name".
    
    If tourneyId is None, return None.
    If tourneyId doesn't exist, return None.
    """
    if tourneyId is None:
        return None
       
    # Try refreshing data if we can't find it
    if tourneyId not in tourneyDatas:
        refreshTournamentData(tourneyId)
    
    # If we still can't find it then it doesn't exist
    if tourneyId not in tourneyDatas:
        return None
    
    return tourneyDatas[tourneyId]['name']

def getTournamentURL(tourneyId):
    """
    Get a tournament's challonge URL.
    """
    if tourneyId is None:
        return None
       
    # Try refreshing data if we can't find it
    if tourneyId not in tourneyDatas:
        refreshTournamentData(tourneyId)
    
    # If we still can't find it then it doesn't exist
    if tourneyId not in tourneyDatas:
        return None
    
    return tourneyDatas[tourneyId]['full-challonge-url']

def getMatchData(tourneyId, matchId):
    """
    Get data for a match.
    
    If matchId or tourneyId are None, return None.
    If matchId or tourneyId don't exist, return None.
    """
    # None if either are None
    if None in (tourneyId, matchId):
        return None
    
    # Try refreshing index data if we can't find it
    if tourneyId not in matchDatas \
            or matchId not in matchDatas[tourneyId]:
        refreshMatchIndex()
    
    # If we still can't find it then it doesn't exist
    if tourneyId not in matchDatas \
            or matchId not in matchDatas[tourneyId]:
        return None

    return matchDatas[tourneyId][matchId]
    
def getParticipantData(tourneyId, participantId):
    """
    Get data for a participant.
    
    If participantId or tourneyId are None, return None.
    If participantId or tourneyId don't exist, return None.
    """
    # None if either are None
    if None in (tourneyId, participantId):
        return None
    
    # Convert just in case
    participantId = int(participantId)
    
    # Try refreshing data if we can't find it
    if tourneyId not in participantDatas \
            or participantId not in participantDatas[tourneyId]:
        refreshParticipantIndex(tourneyId)
        
    # If we still can't find one then it doesn't exist
    if tourneyId not in participantDatas \
            or participantId not in participantDatas[tourneyId]:
        return None

    return participantDatas[tourneyId][participantId]
    
def getLobbyData(tourneyId, matchId):
    """
    Get lobby data for a given match, or if it doesn't exist, create it and
    store it in lobbyDatas.
    """
    matchPair = (tourneyId, matchId)
    
    if matchPair in lobbyDatas:
        return lobbyDatas[matchPair]

    # Not found, so make a new lobby
    matchData = getMatchData(tourneyId, matchId)

    # Get participant info
    # Being paranoid about converting to int..
    p1Id = int(matchData['player1-id']) if matchData['player1-id'] else None
    p2Id = int(matchData['player2-id']) if matchData['player2-id'] else None
    p1Data = getParticipantData(tourneyId, p1Id)
    p2Data = getParticipantData(tourneyId, p2Id)
    
    # Only add if we have participant data
    pDatas = [p for p in [p1Data, p2Data] if p is not None]
    
    prereqData = None
    prereqIds = [matchData['player1-prereq-match-id'], matchData['player2-prereq-match-id']]
    
    # Check if there's an unfinished prerequisite match
    # Don't check ids that are None
    for checkId in [id for id in prereqIds if id]:
        checkData = getMatchData(tourneyId, checkId)
        
        # No winner, so this is unfinished
        if not checkData['winner-id']:
            prereqData = checkData
            break
        
    lobbyData = {
        'participants': [
            {
                'name': playerData['display-name'],
                'id': playerData['id'],
                'seed': playerData['seed'],
                'ready': False,
                'wins': 0,
                'avatar': getParticipantAvatar(playerData)
            } for playerData in pDatas
        ],
        
        # Players are individual users, while participants may be teams (though we don't support them yet).
        # For now, they're basically the same, but this field holds data that would only apply to one person.
        'players': [
            {
                'name': playerData['display-name'],
                'status': 'Online' if playerData['id'] in onlineUsers else 'Offline',
                'legend': 'none'
            } for playerData in pDatas
        ],
        
        'state': {
            'name': 'waitingForMatch',
            'matchNumber': matchIdToNumber(prereqData['identifier']),
            'participantNames': [
                getParticipantData(tourneyId, prereqData['player1-id'])['display-name'],
                getParticipantData(tourneyId, prereqData['player2-id'])['display-name']
            ]
        } if prereqData else {
            'name': 'waitingForPlayers'
        },
        
        'chatlog': [],
        'realmBans': [],

        'bestOf': 3, # TODO: make this configurable
        'startTime': datetime.datetime.now().isoformat(),
        'challongeId': matchIdToNumber(matchData['identifier']),
        'roomNumber': None,
        'currentRealm': None
    }
    
    lobbyDatas[matchPair] = lobbyData
    
    return lobbyData

def getParticipants(tourneyId):
    """
    Get tuple of (name, id) for participants in a tourney.
    
    If tourneyId is None, return None.
    If tourneyId doesn't exist, return None.
    
    Might need to be extended to return more data
    """
    if tourneyId is None:
        return None
        
    # Try refreshing data if we can't find it
    if tourneyId not in participantDatas:
        refreshParticipantIndex(tourneyId)
    
    # If we still can't find one then it doesn't exist
    if tourneyId not in participantDatas:
        return None

    pDatas = participantDatas[tourneyId]
    data = [(pDatas[p]['name'], int(pDatas[p]['id'])) \
        for p in pDatas]
    
    return data
    
def getParticipantMatch(tourneyId, participantId):
    """
    Get a participants current match.
    
    If tourneyId or participantId are None, return None.
    If tourneyId or participantId don't exist, return None.
    
    Returns None if no valid match could be found.
    Returns the matchID as an *INT*.
    """
    if None in (tourneyId, participantId):
        return None
    
    # Try refreshing data if we can't find it
    if tourneyId not in matchDatas:
        refreshMatchIndex(tourneyId)
    
    # If we still can't find it then it doesn't exist
    if tourneyId not in matchDatas:
        return None
    
    # Convert just in case
    participantId = int(participantId)
    
    matchId = None
    mDatas = matchDatas[tourneyId]
    for match in mDatas:
        matchData = mDatas[match]
        
        # Being paranoid about ints again
        p1Id = int(matchData['player1-id']) if matchData['player1-id'] else None
        p2Id = int(matchData['player2-id']) if matchData['player2-id'] else None
        
        pDatas = [p for p in [p1Id, p2Id] if p is not None]

        if participantId in pDatas and matchData['winner-id'] is None:
            matchId = match
            break
    
    return int(matchId)
    
def getParticipantAvatar(pData):
    """
    Build the avatar URL for a participant.
    """
    gravatarBase = 'http://www.gravatar.com/avatar/{}?d=identicon'
    
    # Note the 'or' here. If the player has no email hash, we use their
    # participant ID as a unique Gravatar hash.
    return gravatarBase.format(pData['email-hash'] or pData['id'])

# +--------------------+
# | Set data functions |
# +--------------------+

def _setMatchScore(tourneyId, matchId, score, winner):
    """
    Internal function, only brawlapi functions should touch this.
    
    Updates challonge score for a specific match in a tournament.
    Score is tuple of participant score, with participant one at index 0.
    
    Match data will be refreshed.
    
    No return.
    """
    try:
        challonge.matches.update(tourneyId, matchId,
            scores_csv = '{}-{}'.format(score[0], score[1]),
            winner_id = winner)
        refreshMatchData(tourneyId, matchId)
    except HTTPError as e:
        print('Got {} - {} while updating match score. tID: {}, mID{}'
            .format(e.code, e.reason, tourneyId, matchId))
            
# +-----------------------+
# | Update data functions |
# +-----------------------+

def incrementMatchScore(tourneyId, matchId, participantId):
    """
    Update the score in for a specific match in a tournament.
    Adds 1 to participantId's match score.
    """
    lData = lobbyDatas[(tourneyId, matchId)]
    
    for pLobbyData in lData['participants']:
        if pLobbyData['id'] == participantId:
            pLobbyData['wins'] += 1
            break
    else:
        print('Failed to increment score for tID: {}, mID: {}, pID: {}')
    
    # Handle _setMatchScore here

def addChatMessage(tourneyId, matchId, messageData):
    """
    Add a message to the chat log for a specific match in a tournament.
    
    No return
    """
    lData = lobbyDatas.get((tourneyId, matchId), None)
    if lData is None:
        print('Couldn\'t find lobby data while updating log. mID: {}, tID: {}'
            .format(matchId, tourneyId))
        return
    
    lData['chatlog'].append(messageData)
    
def init_example_db():
    db = db_wrapper.DBWrapper('dbname', filepath='.')
    
    if not db.table_exists('test_table'):
        # https://www.sqlite.org/datatype3.html
        db.create_table(
            'tablename',
            ['field1', 'field2'],
            ['INTEGER', 'TEXT'],
            'field1') # primary field
            
        assert(db.table_exists('tablename'))
        
        db.insert_values('tablename', [('1', 'test'),
                                       (2, 'test2'), 
                                       (3, 'test3')])

        db.delete_values('tablename', 'field2 = 3')
