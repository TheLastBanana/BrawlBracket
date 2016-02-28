import bracket.tournament
import bidict

_tournaments = bidict()

def createTournament(shortName, **kwargs):
    """
    Creates a tournament.
    shortName: This tournament's unique shortName (string)
    
    Returns the new Tournament.
    Returns None if the shortName wasn't unique.
    """
    if shortName in _tournaments:
        return None
    
    tournament = bracket.tournament.SingleElimTournament(shortName, **kwargs)
    
    _tournaments.[shortName] = tournament
    
    return tournament
    
def getTournament(id):
    """
    Gets a tournament by uuid.
    
    Returns None if no tournament was found.
    Returns the tournament found.
    """
    for tournament in _tournaments:
        if tournament.id == id:
            return tournament

def tournamentNameExists(shortName):
    """
    Check if a tournament name exists.
    
    shortName: Tournament shortName to check.
    
    Returns True if the shortName is in use, False otherwise.
    """
    return shortName in _tournaments
