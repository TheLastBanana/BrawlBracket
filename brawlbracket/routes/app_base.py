from flask import session
from flask import redirect
from flask import url_for
from flask import render_template
from flask import abort

from brawlbracket.app import app
from brawlbracket import usermanager as um
from brawlbracket import tournamentmanager as tm
from brawlbracket import util

from brawlbracket.routes import app_admin
from brawlbracket.routes import app_player

# Base app page
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
    
    
    return render_template('app/app.html',
                           startPage=startPage,
                           tourneyName=tourneyName,
                           tournament=tournament,
                           basePath='/t/{}/app/'.format(tourneyName))