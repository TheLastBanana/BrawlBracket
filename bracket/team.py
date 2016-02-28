import uuid

class Team:
    """
    A seeded entry in the tournament. Create these through the Tournament class.
    """
    def __init__(self, seed, players = None, **kwargs):
        """
        Team data:
         id: BrawlBracket id (uuid)
         seed: Tournament seeding (int)
         name: Team name (string)
         players: Players on this team (list of Player)
        
        Tournament data:
         eliminated: Has this team been eliminated (boolean)
         checkedIn: Has this team checked in (boolean)
        """
        self.id = kwargs.get('uuid', uuid.uuid1())
        
        self.seed = seed
        self.name = kwargs.get('name')
        
        if players is None:
            self.players = []
        else:
            self.players = players
        
        self.eliminated = False
        self.checkedIn = False
        
    def __repr__(self):
        return '{} ({})'.format(self.name, self.seed)