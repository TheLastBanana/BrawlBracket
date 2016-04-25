from flask import session
from flask import redirect
from flask import url_for
from flask import render_template
from flask import abort
from flask import g

from brawlbracket.app import app
from brawlbracket import usermanager as um
from brawlbracket import tournamentmanager as tm
from brawlbracket import util

print('Registering user pages routes...')

# Contact admin page
@app.route('/app-pages/contact-admin/<tourneyName>')
def contact_admin():
    return render_template('app/pages/contact-admin.html',
                           tournament=g.tournament,
                           tourneyName=g.tourneyName)
    
# App version of tournament index
@app.route('/app-pages/index/<tourneyName>')
def app_tournament_index():
    return render_template('app/pages/tournament-index.html',
                           tourneyName=g.tourneyName,
                           tournament=g.tournament)
    
# Lobby content
@app.route('/app-pages/lobby/<tourneyName>')
def lobby():
    return render_template('app/pages/lobby.html',
                           tournament=g.tournament,
                           tourneyName=g.tourneyName,
                           legendData=util.orderedLegends,
                           realmData=[(id, util.realmData[id]) for id in util.eslRealms])