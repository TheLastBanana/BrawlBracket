from flask import Flask  
from flask import render_template  
from flask import request
from flask import abort
from bidict import bidict

import os
import challonge

# Bi-directional map from tournament's Challonge URL suffix to its ID.
# We'll actually build this from the Challonge API later.
tourneys = bidict({ 'thelastbanana_test': '2119181' })

challonge.set_credentials(os.environ.get('BB_CHALLONGE_USER'), os.environ.get('BB_CHALLONGE_API_KEY'))

app = Flask(__name__)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')

# Login in a tourney participant
@app.route('/login/<tourneyName>')             
def user_login(tourneyName):
    if tourneyName not in tourneys:
        abort(404)

    tourneyId = tourneys[tourneyName]
    tourneyData = challonge.tournaments.show(tourneyId)
    prettyName = tourneyData['name']
    tourneyURL = tourneyData['full-challonge-url']
    
    participants = challonge.participants.index(tourneyId)
    participantNames = [ participant['name'] for participant in participants ]
    
    # Boolean value is whether the user is already logged in
    participantPairs = [(name, False) for name in participantNames]

    return render_template('user-login.html',
                           tourneyName=prettyName,
                           participants=participantPairs,
                           challongeURL=tourneyURL)

if __name__ == '__main__':
    app.debug = True
    app.run()