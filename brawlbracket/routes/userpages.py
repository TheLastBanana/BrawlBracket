from flask import session
from flask import redirect
from flask import url_for
from flask import render_template
from flask import abort

from brawlbracket.app import app
from brawlbracket import usermanager as um
from brawlbracket import tournamentmanager as tm
from brawlbracket import util

print('Registering user pages routes...')

# User app page
@app.route('/t/<tourneyName>/app/', defaults={'startPage': None})
@app.route('/t/<tourneyName>/app/<startPage>/')
def user_app(tourneyName, startPage):
    if not tm.tournamentNameExists(tourneyName):
        abort(404)
    
    userId = session.get('userId', None)
    user = um.getUserById(userId)
    if user is None:
        print('User doesn\'t exist; returned to index.')
        return redirect(url_for('tournament_index', tourneyName=tourneyName))

    tournament = tm.getTournamentByName(tourneyName)
    session['tourneyId'] = tournament.id
    
    
    return render_template('app/user-app.html',
                           startPage=startPage,
                           tourneyName=tourneyName,
                           tournament=tournament,
                           basePath='/t/{}/app/'.format(tourneyName))

# Contact admin page
@app.route('/app-pages/contact-admin/<tourneyName>')
def contact_admin(tourneyName):
    tournament = tm.getTournamentByName(tourneyName)
    return render_template('app/pages/contact-admin.html',
                           tournament=tournament,
                           tourneyName=tourneyName)
    
# App version of tournament index
@app.route('/app-pages/index/<tourneyName>')
def app_tournament_index(tourneyName):
    tournament = tm.getTournamentByName(tourneyName)

    return render_template('app/pages/tournament-index.html',
                           tourneyName=tourneyName,
                           tournament=tournament)
    
# Lobby content
@app.route('/app-pages/lobby/<tourneyName>')
def lobby(tourneyName):
    tournament = tm.getTournamentByName(tourneyName)
    return render_template('app/pages/lobby.html',
                           tournament=tournament,
                           tourneyName=tourneyName,
                           legendData=util.orderedLegends,
                           realmData=[(id, util.realmData[id]) for id in util.eslRealms])