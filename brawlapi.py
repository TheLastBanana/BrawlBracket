import os
import datetime
import uuid
from urllib.error import HTTPError

import challonge

import db_wrapper
import util

# Player settings JSON objects
allPlayerSettings = {}

# Set up challonge
challonge.set_credentials(os.environ.get('BB_CHALLONGE_USER'), os.environ.get('BB_CHALLONGE_API_KEY'))

# Cached Challonge data
tourneyDatas = {}
matchDatas = {}
participantDatas = {} # Has raw challonge participant data
userDatas = {} # Has BrawlBracket created user data
lobbyDatas = {}

# Set of online participant IDs
onlineUsers = set()

# All chat logs
chats = {}

# Admin secret keys for each tourney
adminKeys = {
    '2119181': ['GREATPASSWORDM8']
}

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
    
# +---------------+
# | Chat Managing |
# +---------------+
class Chat:
    """
    Holds data about a chat.
    """
    
    def __init__(self, id):
        """
        Create the chat with a unique id.
        """
        # Unique id
        self.id = id
        
        # JSON message data
        self.log = []
        
    def getRoom(self):
        """
        Get the socketIO name of the chat room.
        """
        
        return 'chat-{}'.format(self.id)
        
    def addMessage(self, data):
        """
        Add message data to the chat log.
        """
        self.log.append(data)

def createChat(tourneyId):
    """
    Add a chat to the tourney. Returns the chat's id.
    """
    chatPair = None
    chatId = None
    
    while chatPair is None or ((tourneyId, id) in chats):
        chatId = str(uuid.uuid4())
        chatPair = (tourneyId, chatId)
        
    chats[chatPair] = Chat(chatId)
        
    return chatId
    
def getChat(tourneyId, chatId):
    """
    Get a chat in a tourney.
    """
    chatPair = (tourneyId, chatId)
    
    if chatPair not in chats:
        return
    
    return chats[chatPair]

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
        pDatas = {}
        uDatas = {}
        pIndex = challonge.participants.index(tourneyId)
        
        for pData in pIndex:
            # Convert to int
            pId = int(pData['id'])
            
            pDatas[pId] = pData
            uDatas[pId] = util.User(participantId=pId)
            
        participantDatas[tourneyId] = pDatas
        userDatas[tourneyId] = uDatas
    
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
        
        # Note: We assume here that if we've seen user before that they've
        #       been correctly set up. We also assume that the data we're saving
        #       about the user doesn't change (pId). If this assumption is no
        #       longer true, we must change this.
        if paritipantId not in userDatas[tourneyId]:
            uData = User(participantId=int(participantId))
            userDatas[tourneyId][participantId] = uData
            
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

def getTournamentLiveImageURL(tourneyId):
    """
    Get a tournament's live image URL.
    """
    if tourneyId is None:
        return None
       
    # Try refreshing data if we can't find it
    if tourneyId not in tourneyDatas:
        refreshTournamentData(tourneyId)
    
    # If we still can't find it then it doesn't exist
    if tourneyId not in tourneyDatas:
        return None
    
    return tourneyDatas[tourneyId]['live-image-url']
    
def getTournamentMatches(tourneyId):
    """
    Return a dictionary from match id to match data for a tournament.
    """
    
    if tourneyId not in matchDatas:
        refreshMatchIndex(tourneyId)
        
    return matchDatas[tourneyId]
    
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
        refreshMatchIndex(tourneyId)
    
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

def getPlayerSettings(tourneyId, playerId):
    """
    Get a player's settings.
    TODO: playerIds and participantIds are separate if participants = teams.
    """
    playerPair = (tourneyId, playerId)

    if playerPair in allPlayerSettings:
        return allPlayerSettings[playerPair]

    playerSettings = {
        'preferredServer': 'na',
        # Just send legend internal ids
        'ownedLegends': util.ownableLegendIds
    }

    allPlayerSettings[playerPair] = playerSettings

    return playerSettings

def getLobbyData(tourneyId, matchId):
    """
    Get lobby data for a given match, or if it doesn't exist, create it and
    store it in lobbyDatas.
    """
    
    matchPair = (tourneyId, matchId)
    
    if lobbyExists(tourneyId, matchId):
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
            
    if prereqData:
        prereqMatchNum = matchIdToNumber(prereqData['identifier'])
        
        prereqP1Data = getParticipantData(tourneyId, prereqData['player1-id'])
        prereqP1Name = prereqP1Data['display-name'] if prereqP1Data else '?'
        
        prereqP2Data = getParticipantData(tourneyId, prereqData['player2-id'])
        prereqP2Name = prereqP2Data['display-name'] if prereqP2Data else '?'
        
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
            'matchNumber': prereqMatchNum,
            'participantNames': [
                prereqP1Name,
                prereqP2Name
            ]
        } if prereqData else {
            'name': 'waitingForPlayers'
        },
        
        'chatId': None,
        'realmBans': [],

        'bestOf': 3, # TODO: make this configurable
        'startTime': datetime.datetime.now().isoformat(),
        'challongeId': matchIdToNumber(matchData['identifier']),
        'roomNumber': None,
        'currentRealm': None
    }
    
    lobbyDatas[matchPair] = lobbyData
    
    return lobbyData

def getLobbyPrettyState(tourneyId, matchId):
    """
    Get a nicely formatted summary of a lobby's state.
    """
    if not lobbyExists(tourneyId, matchId):
        return 'Does not exist'
        
    lobbyData = getLobbyData(tourneyId, matchId)
    stateName = lobbyData['state']['name']
    
    
    if stateName == 'waitingForMatch':
        return 'Waiting for match #{}'.format(lobbyData['state']['matchNumber'])
        
    elif stateName == 'waitingForPlayers':
        # Show participant names -- all player names in e.g. 2v2s would make a really long string
        participants = lobbyData['participants']
        
        notReady = []
        for participant in participants:
            if not participant['ready']:
                notReady.append(participant['name'])
        
        # We assume there are only 2 participants in a lobby
        if len(notReady) == 2:
            return 'Waiting for both participants'
            
        return 'Waiting for {}'.format(notReady[0])
        
    return 'Unknown'
    
def lobbyExists(tourneyId, matchId):
    """
    Return true if a lobby exists.
    """
    matchPair = (tourneyId, matchId)
    
    return matchPair in lobbyDatas
    
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

def getUser(tourneyId, participantId):
    """
    Gets a User associated with a tournament.
    
    If participantId or tourneyId are None, return None.
    If participantId or tourneyId don't exist, return None.
    """
    # None if either are None
    if None in (tourneyId, participantId):
        return None
    
    # Don't have the tournament participant.
    # Can just refresh data, it will get the whole cache if it hasn't been
    # downloaded yet.
    if tourneyId not in userDatas or\
            participantId not in userDatas[tourneyId]:
        refreshParticipantData(tourneyId)
    
    # Either the tournament or the participant couldn't be found.
    if tourneyId not in userDatas or\
            participantId not in userDatas[tourneyId]:
        return None
    
    for user in userDatas[tourneyId]:
        if user.participantId == participantId:
            return user


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
    
    No return.
    """
    lData = lobbyDatas.get((tourneyId, matchId), None)
    if lData is None:
        print('Couldn\'t find lobby data while updating score. mID: {}, tID: {}'
            .format(matchId, tourneyId))
        return
    
    for pLobbyData in lData['participants']:
        if pLobbyData['id'] == participantId:
            pLobbyData['wins'] += 1
            break
    else:
        print('Failed to increment score for pID: {}, mID: {}, tID: {}'
            .format(participantId, matchId, tourneyId))
    
    # Handle _setMatchScore here
    
def setPlayerSettings(tourneyId, playerId, settings):
    """
    Validate and overwrite player settings. Return true if the settings were
    valid and were updated, else false.
    """
    playerPair = (tourneyId, playerId)
    
    if settings['preferredServer'] not in util.serverRegions:
        return False
        
    for legend in settings['ownedLegends']:
        if legend not in util.ownableLegendIds:
            return False
    
    allPlayerSettings[playerPair] = settings
    return True
    
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
