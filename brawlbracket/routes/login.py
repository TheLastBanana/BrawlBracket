import re

from flask import session
from flask import redirect
from flask import url_for
from flask import g

from brawlbracket.app import app
from brawlbracket.app import oid
from brawlbracket import usermanager as um

print('Registering login routes...')

_steam_id_re = re.compile('steamcommunity.com/openid/id/(.*?)$')

@app.route('/login/')
@oid.loginhandler
def login():
    if g.user is None:
        if g.userId is not None:
            session.pop('userId')
        
        return oid.try_login('http://steamcommunity.com/openid')
    else:
        return redirect(oid.get_next_url())

@app.route('/logout/')
def logout():
    session.pop('userId')
    return redirect(oid.get_next_url())

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