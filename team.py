class Team:
    """
    A Team in a tournament. This will be linked to a single Match at a time but
    will be passed along as the team progresses in the tournament.
    """
    def __init__(self, uuid, seed, name):
        """
        Team data:
         id: BrawlBracket id (uuid)
         seed: Tournament seeding (int)
         name: Team name (string)
         players: Players on this team (list of players)
        
        Tournament data:
         eliminated: Has this team been eliminated (boolean)
         checkedIn: Has this team checked in (boolean)
        """
        self.id = uuid
        self.seed = seed
        self.name = name
        self.players = []
        self.eliminated = False
        self.checkedIn = False