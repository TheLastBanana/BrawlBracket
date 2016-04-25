from functools import wraps

from flask import Flask
from flask import g
from flask import session
from flask import abort

from brawlbracket.app import app
from brawlbracket import usermanager as um

def tourney_admin_only(f):
    """
    Abort with a 403 error if the g.user is not an admin of g.tournament.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not g.user or not g.tournament or not g.tournament.isAdmin(g.user):
            abort(403)
            
        return f(*args, **kwargs)
        
    return decorated_function