import json

from flask import session
from flask import redirect
from flask import url_for
from flask import render_template
from flask import request
from flask import abort
from flask import g

from brawlbracket.app import app
from brawlbracket import usermanager as um
from brawlbracket import tournamentmanager as tm
from brawlbracket import util

print('Registering root routes...')

@app.route('/')
@app.route('/index/')
def index():
    userId = session.get('userId', None)
    user = um.getUserById(userId)
    if user is not None:
        return render_template('user-tournaments.html')
        
    else:
        return render_template('index.html')
        brawlapi.init_example_db()
    
# Settings page
@app.route('/settings/', methods=['GET', 'PUT'])
def user_settings():
    userId = session.get('userId', None)
    user = um.getUserById(userId)
    
    if user is None:
        print('User doesn\'t exist; returned to index.')
        return redirect(url_for('index'))
    
    if request.method == 'GET':
        return render_template('settings.html',
                               legendData=util.orderedLegends,
                               serverRegions=util.orderedRegions)
                               
    elif request.method == 'PUT':
        if user.setSettings(request.json):
            return json.dumps({'success': True}), 200
            
        else:
            return json.dumps({'success': False}), 500

# Tournament index page
@app.route('/t/<tourneyName>/')
def tournament_index():
    return render_template('tournament.html',
                           tourneyName=g.tourneyName,
                           tournament=g.tournament)

@app.route('/t/<tourneyName>/register', methods=['POST'])
def register():
    userId = session.get('userId')
    user = um.getUserById(userId)

    # Not logged in and trying to register
    if user is None:
        return

    existing = False
    for player in g.tournament.players:
        if player.user.id == user.id:
            existing = True
            break

    if not existing:
        team = g.tournament.createTeam(
            len(g.tournament.teams) + 1,
            name = user.username)
        
        player = g.tournament.createPlayer(user)
        
        team.addPlayer(player)
        
        print('ADDED TEAM: {}, PLAYERS: {}'.format(team, team.players))
        print('TOURNAMENT NOW HAS {} TEAMS'.format(len(g.tournament.teams)))
    else:
        print('ADD TEAM FAILED, ALREADY JOINED! {}'.format(user.username))
        
    return redirect(url_for('tournament_index', tourneyName=g.tourneyName))
    
# TODO: Make this POST-only to avoid accidental finalizes (once we have an actual button for it)
@app.route('/t/<tourneyName>/finalize')
def finalize():
    userId = session.get('userId', None)
    user = um.getUserById(userId)
    if user is None:
        print('User doesn\'t exist; returned to index.')
        return redirect(url_for('tournament_index', tourneyName=g.tourneyName))
    
    if g.tournament.isAdmin(user):
        print('FINALIZING TOURNAMENT')
        print('Tournament has {} users!'.format(len(g.tournament.teams)))
        g.tournament.generateMatches()
        print(g.tournament)
        print('Tournament has {} matches!'.format(len(g.tournament.matches)))
    
    return redirect(url_for('tournament_index', tourneyName=g.tourneyName))