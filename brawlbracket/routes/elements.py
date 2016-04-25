from flask import render_template

from brawlbracket.app import app
from brawlbracket import util

print('Registering elements routes...')
    
# Connect error
@app.route('/app-elements/lobby-error/<tourneyName>')
def lobby_error():
    return render_template('app/elements/lobby-error.html')
    
# Legend roster
@app.route('/app-elements/roster')
def roster():
    return render_template('app/elements/lobby-roster.html',
    legendData=util.orderedLegends)
    
# Realm picker
@app.route('/app-elements/realms')
def realms():
    return render_template('app/elements/lobby-realms.html',
                           realmData=util.orderedRealms)