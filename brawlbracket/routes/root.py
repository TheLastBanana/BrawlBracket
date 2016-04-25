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

from brawlbracket.viewdecorators import *

print('Registering root routes...')

@app.route('/')
@app.route('/index/')
def index():
    if g.user is not None:
        return render_template('user-tournaments.html')
        
    else:
        return render_template('index.html')
        brawlapi.init_example_db()
    
# Settings page
@app.route('/settings/', methods=['GET', 'PUT'])
def user_settings():
    if g.user is None:
        print('User doesn\'t exist; returned to index.')
        return redirect(url_for('index'))
    
    if request.method == 'GET':
        return render_template('settings.html',
                               legendData=util.orderedLegends,
                               serverRegions=util.orderedRegions)
                               
    elif request.method == 'PUT':
        if g.user.setSettings(request.json):
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
    # Not logged in and trying to register
    if g.user is None:
        return

    existing = False
    for player in g.tournament.players:
        if player.user.id == g.user.id:
            existing = True
            break

    if not existing:
        team = g.tournament.createTeam(
            len(g.tournament.teams) + 1,
            name = g.user.username)
        
        player = g.tournament.createPlayer(g.user)
        
        team.addPlayer(player)
        
        print('ADDED TEAM: {}, PLAYERS: {}'.format(team, team.players))
        print('TOURNAMENT NOW HAS {} TEAMS'.format(len(g.tournament.teams)))
    else:
        print('ADD TEAM FAILED, ALREADY JOINED! {}'.format(g.user.username))
        
    return redirect(url_for('tournament_index', tourneyName=g.tourneyName))
    
# TODO: Make this POST-only to avoid accidental finalizes (once we have an actual button for it)
@app.route('/t/<tourneyName>/finalize')
@tourney_admin_only
def finalize():
    if g.user is None:
        print('User doesn\'t exist; returned to index.')
        return redirect(url_for('tournament_index', tourneyName=g.tourneyName))
    
    print('FINALIZING TOURNAMENT')
    print('Tournament has {} users!'.format(len(g.tournament.teams)))
    g.tournament.generateMatches()
    print(g.tournament)
    print('Tournament has {} matches!'.format(len(g.tournament.matches)))
    
    return redirect(url_for('tournament_index', tourneyName=g.tourneyName))