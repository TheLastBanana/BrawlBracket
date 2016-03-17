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
        self.name = kwargs.get('name', '')
        
        # addPlayer, removePlayer
        if players is None:
            self.players = []
        else:
            self.players = players
        
        self.eliminated = False
        self.checkedIn = False

    def __setattr__(self, name, value):
        """
        Override default setting value functionality to let us send things to
        the database on updates.
        """
        super().__setattr__(name, value)
        
        # Could be picky about names of vars changing where we don't want to 
        # write out to the database
        if name in ['_dbCallback']:
            return
        
        if '_dbCallback' in self.__dict__ and self._dbCallback is not None:
            self._dbCallback(self)
        
    def __repr__(self):
        return '{} ({})'.format(self.name, self.seed)

    def addPlayer(self, player):
        """
        Add player to this team.
        """
        if player in self.players:
            return
        
        self.players.append(player)
        if '_dbCallback' in self.__dict__ and self._dbCallback is not None:
            self._dbCallback(self)
    
    def removePlayer(self, player):
        """
        Remove player from this team.
        """
        if player not in self.players:
            return
        
        self.players.remove(player)
        if '_dbCallback' in self.__dict__ and self._dbCallback is not None:
            self._dbCallback(self)
        