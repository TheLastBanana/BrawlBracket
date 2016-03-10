import os
import json
import uuid

import requests

from brawlbracket import user
from brawlbracket import db_wrapper
from brawlbracket import util

_users = []

_db = None

def createUser(steamId):
    """
    Takes a steamId and turns it into a BrawlBracketUser.
    
    Raises ValueError if a user already exists with this steamId.
    
    Returns None if the steam request fails for some reason.
    Returns the created User on success
    """
    for u in _users:
        if u.steamId == steamId:
            raise ValueError('User already exists with steamId! {}'.format(u))
    
    steamInfo = _getSteamInfo(steamId)
    if steamInfo is None:
        return None
    
    name = steamInfo['personaname']
    avatar = steamInfo['avatarfull']
    
    newUser = user.User(steamId, name, avatar)
    
    _writeUserToDB(newUser)
    
    _users.append(newUser)
    
    return newUser

def getUserById(id):
    """
    Gets user by uuid.
    
    Returns None if the uuid isn't associated with a user.
    Returns User otherwise.
    """
    if id is None:
        return None
    
    for u in _users:
        if u.id == id:
            return u
    
    return None
    
def getUserBySteamId(steamId):
    """
    Gets user by steamId.
    
    Returns None if the steamId isn't associated with a user.
    Returns User otherwise.
    """
    if id is None:
        return None
    
    # Check cache first
    for u in _users:
        if u.steamId == steamId:
            print('return u')
            return u
    
    # Check DB last'
    u = _getUserFromDBBySteamId(steamId)
    if u is not None:
        _users.append(u)
        return u
    
    return None

def _getSteamInfo(steamId):
    """
    Takes a steamId and returns info about the steam user.
    
    Returns None if the request fails, the user doesn't exist, or if the
    response is malformed.
    """
    options = {'key': os.environ.get('BB_STEAM_API_KEY'),
               'steamids': steamId}

    url = 'http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/'
    
    rv = requests.get(url, params=options)
    
    try:
        # This raises an HTTPError if the request got anything except 200
        rv.raise_for_status()
        
        rv = rv.json()

        if len(rv['response']['players']) > 0:
            return rv['response']['players'][0]
        else:
            return None
    # Couldn't parse json
    except ValueError as e:
        return None
    # Request error
    except requests.exceptions.HTTPError as e:
        print('Bad steam request! {} {}'.format(url, options))
        return None

def _getUserFromDBById(id):
    """
    """
    raise NotImplementedError('Can\'t getUserFromDBById')

def _getUserFromDBBySteamId(steamId):
    """
    Gets a user from the database by steamId.
    
    Returns user if user was in database
    Returns None otherwise
    """
    if _db is None:
        _initDB()
    
    rows = _db.select_values('users', ['*'], ['steamId = {}'.format(steamId)])
    
    if rows:
        userData = rows[0]
        print('Making user from: ', userData)
        id = userData[0]
        steamId = userData[1]
        username = userData[2]
        avatar = userData[3]
        ownedLegends = json.loads(userData[4])
        preferredServer = userData[5]
        
        u = user.User(steamId, username, avatar, uuid=id)
        
        # Don't use setSettings because we don't want validation and we
        # don't want to be renotified that we've updated
        u.preferredServer = preferredServer
        u.ownedLegends = ownedLegends
        
        return u
    else:
        return None
        
def _writeUserToDB(u):
    """
    Serializes a user and then inserts it into the user table of the database.
    """
    if _db is None:
        _initDB()
    
    userData = (
        u.id,
        u.steamId,
        u.username,
        u.avatar,
        json.dumps(u.ownedLegends),
        u.preferredServer
        )
    print('Writing user with: ', userData)
    _db.insert_values('users', [userData])
        
def _initDB():
    print('----INIT USER DATABASE----')
    # Need to global because _db is not local to this context
    global _db
    _db = db_wrapper.DBWrapper(util.dbName, filepath=util.dbPath)
    
    # Make user table
    if not _db.table_exists('users'):
        fieldNames = [
            'id',
            'steamId',
            'username',
            'avatar',
            'ownedLegends',
            'preferredServer'
            ]
        fieldTypes = [
            'UUID',
            'INTEGER',
            'TEXT',
            'TEXT',
            'TEXT',
            'TEXT'
            ]
            
        _db.create_table('users', fieldNames, fieldTypes, 'id')

if __name__ == '__main__':
    steamIds = [76561198042414835, 76561198078549692, 76561197993702532,
                76561198069178478, 76561198065399638, 76561197995127703,
                76561198068388037, 76561198050490587, 76561198072175457,
                76561198063265824, 76561198042403860]
    
    for id in steamIds:
        print(createUser(id))