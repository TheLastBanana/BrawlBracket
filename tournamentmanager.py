import bracket.tournament
import bidict

_tournamentsByName = bidict.bidict()
_tournaments = []

def createTournament(shortName, **kwargs):
    """
    Creates a tournament.
    shortName: This tournament's unique shortName (string)
    
    Returns the new Tournament.
    Returns None if the shortName wasn't unique.
    """
    if shortName in _tournamentsByName:
        return None
    
    tournament = bracket.tournament.SingleElimTournament(shortName, **kwargs)
    
    _tournamentsByName[shortName] = tournament.id
    _tournaments.append(tournament)
    
    return tournament
    
def getTournamentById(id):
    """
    Gets a tournament by uuid.
    
    Returns None if no tournament was found.
    Returns the tournament found.
    """
    for tournament in _tournaments:
        if tournament.id == id:
            return tournament

def getTournamentByName(shortName):
    """
    Gets a tournament by short name.
    
    Returns None if no tournament was found.
    Returns the tournament found.
    """
    id = _tournamentsByName.get(shortName, None)
    if id is None:
        return None
    
    return getTournamentById(id)

def tournamentNameExists(shortName):
    """
    Check if a tournament name exists.
    
    shortName: Tournament shortName to check.
    
    Returns True if the shortName is in use, False otherwise.
    """
    return shortName in _tournamentsByName
