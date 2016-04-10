import json

from flask import session
from flask import redirect
from flask import url_for
from flask import render_template
from flask import abort

from brawlbracket.app import app
from brawlbracket import usermanager as um
from brawlbracket import tournamentmanager as tm

print('Registering admin pages routes...')
                           
# Admin dashboard
@app.route('/app-pages/admin-dashboard/<tourneyName>')
def admin_dashboard(tourneyName):
    tournament = tm.getTournamentByName(tourneyName)
    userId = session.get('userId')
    user = um.getUserById(userId)
    
    if tournament is None:
        abort(404)
    
    if user is None:
        return redirect(url_for('tournament_index', tourneyName = tourneyName))
    
    if not tournament.isAdmin(user):
        abort(403)

    return render_template('app/pages/admin-dashboard.html',
                           tournament=tournament,
                           tourneyName=tourneyName)

# Lobby data
@app.route('/app-data/lobbies/<tourneyName>')
def data_lobbies(tourneyName):
    tournament = tm.getTournamentByName(tourneyName)
    
    if tournament is None:
        abort(404)

    # Get a condensed list of lobby data for display to the admin
    condensedData = []

    for match in tournament.matches:
        # Assemble score string 
        scoreString = '-'.join([str(s) for s in match.score])
            
        # Add on bestOf value (e.g. best of 3)
        scoreString += ' (Bo{})'.format(match.bestOf)
        
        status, prettyStatus, statusOrder = match.lobbyStatus
        
        condensed = {
            'id': match.number,
            't1Name': match.teams[0].name if match.teams[0] is not None else '',
            't2Name': match.teams[1].name if match.teams[1] is not None else '',
            'score': scoreString,
            'room': match.roomNumber if match.roomNumber is not None else '',
            'startTime': match.startTime.isoformat()\
                if match.startTime is not None else '',
            'status': {
                'state': status,
                'display': prettyStatus,
                'sort': statusOrder
            }
        }
        
        condensedData.append(condensed)
        
    ajaxData = {
        'data': condensedData
    }
    
    return json.dumps(ajaxData)
    
# User data
@app.route('/app-data/teams/<tourneyName>')
def data_teams(tourneyName):
    tournament = tm.getTournamentByName(tourneyName)
    
    if tournament is None:
        abort(404)
    
    # Get a condensed list of user data for display to the admin
    condensedData = []
    
    for team in tournament.teams:
        status, prettyStatus = tournament.getTeamStatus(team)
        
        condensed = {
            'seed': team.seed,
            'name': team.name,
            'status': {
                'status': status,
                'display': prettyStatus,
            },
            'online': 'Online' if all([p.online > 0 for p in team.players])\
                      else 'Offline'
        }
        
        condensedData.append(condensed)
        
    ajaxData = {
        'data': condensedData
    }
    
    return json.dumps(ajaxData)