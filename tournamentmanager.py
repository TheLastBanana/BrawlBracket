import bracket.tournament

_tournaments = []

def createTournament(**kwargs):
    """
    Creates a tournament.
    
    Returns the new Tournament.
    """
    tournament = bracket.tournament.Tournament(**kwargs)
    
    _tournaments.append(tournament)
    
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