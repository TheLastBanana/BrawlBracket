import os
import json
import uuid

import requests

import user

_users = []

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
    _users.append(newUser)
    
    return newUser

def getUserById(id):
    """
    Gets user by uuid.
    
    Returns None if the uuid isn't associated with a user.
    Returns User otherwise.
    """
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
    for u in _users:
        if u.steamId == steamId:
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

if __name__ == '__main__':
    steamIds = [76561198042414835, 76561198078549692, 76561197993702532,
                76561198069178478, 76561198065399638, 76561197995127703,
                76561198068388037, 76561198050490587, 76561198072175457,
                76561198063265824, 76561198042403860]
    
    for id in steamIds:
        print(createUser(id))