import eventlet
eventlet.monkey_patch()

import os

from flask import Flask
from flask import g
from flask import render_template
from flask import session
from flask_socketio import SocketIO
from flask.ext.openid import OpenID

from brawlbracket import usermanager as um
from brawlbracket import tournamentmanager as tm

__version__ = '0.1.0'

app = Flask(__name__, static_folder='dist/static', template_folder='dist/templates')
app.root_path = os.path.dirname(os.path.abspath(__file__))
app.secret_key = os.environ.get('BB_SECRET_KEY')
socketio = SocketIO(app)
oid = OpenID(app)

# Import our routes after creating app
from brawlbracket.routes import root
from brawlbracket.routes import login
from brawlbracket.routes import app_base
from brawlbracket.routes import elements
from brawlbracket.routes import tournamentio
from brawlbracket.routes import chatio

# Start temp tournament generation
#steamIds = [76561198045082103, 76561198065399638, 76561198072175457,
#            76561198069178478, 76561198078549692, 76561197995127703,
#            76561198068388037, 76561198042414835, 76561197993702532,
#            76561198063265824, 76561198042403860, 76561198050490587]
#steamIds = [76561197993702532, 76561197995127703, 76561198045082103,
#            76561198042414835]
#tempUsers = []
#for id in steamIds:
#    user = um.getUserBySteamId(id)
#    if user is None:
#        user = um.createUser(id)
#    tempUsers.append(user)

# Generate admins as users
admins = [76561198042414835, 76561197993702532, 76561197995127703]
for id in admins:
    user = um.getUserBySteamId(id)
    if user is None:
        user = um.createUser(id)

tempTourney = tm.getTournamentByName('test')
if tempTourney is None:
    tempTourney = tm.createTournament(
                    'test',
                    name='BrawlBracket Test Tourney'
                    )
    tempTourney.addAdmins(um.getUserBySteamId(76561198042414835), #braaedy
                          um.getUserBySteamId(76561197993702532), #banana
                          um.getUserBySteamId(76561197995127703)) #sweepy
    print('Admins: ', [a.username for a in tempTourney.admins])

#    for i, user in enumerate(tempUsers):
#        team = tempTourney.createTeam(i + 1) # i = seed, 1-indexed
#        team.name = user.username
#        player = tempTourney.createPlayer(user)
#        team.players.append(player)
#        print(team)
#    print('Temp tournament has {} users!'.format(len(tempTourney.teams)))
#    tempTourney.generateMatches()
    
    
# End temp tournament generation
    
@app.context_processor
def default_template_data():
    userId = session.get('userId', None)
    user = um.getUserById(userId)
    
    return dict(versionNumber = __version__,
                user = user)
                
@app.url_value_preprocessor
def pull_tourney(endpoint, values):
    """
    Get the tournament name and object.
    """
    if not values: return
    
    g.tourneyName = values.pop('tourneyName', None)
    g.tournament = None
    if g.tourneyName:
        g.tournament = tm.getTournamentByName(g.tourneyName)
                
@app.template_filter('datetime')
def filter_datetime(date):
    """
    Filter to format a Python datetime.
    """
    return date.strftime('%B %d, %Y @ %I:%M %p %Z')
    
@app.template_filter('timedelta')
def filter_timedelta(time):
    """
    Filter to format a Python timedelta.
    """
    hours, remainder = divmod(time.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    tokens = []
    if hours > 0:
        tokens.append('{} hour'.format(hours) + ('s' if hours > 1 else ''))
        
    if minutes > 0:
        tokens.append('{} minute'.format(minutes) + ('s' if minutes > 1 else ''))
    
    return ', '.join(tokens)
    
#----- Flask routing -----#
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

def runWebServer(debug=False):
    """
    Run the web server.
    """
    app.debug = debug
    socketio.run(app, host='0.0.0.0')
