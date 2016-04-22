import uuid

class Player:
    """
    A Player on a Team in a Tournament. This is linked to a single team in a
    single tournament.
    """
    def __init__(self, user, **kwargs):
        """
        Player data:
         id: BrawlBracket id (uuid)
         user: BrawlBracket user (User)
        
        Tournament data:
         currentLegend: currently selected legend (string id)
         online: number of live connections (int)
         adminChat: private chat with admin, which will be created by the tournament (Chat)
        """
        self.id = kwargs.get('uuid', uuid.uuid1())
        self.user = user
        self.currentLegend = None
        self.online = 0 # Change my name probably
        self.adminChat = None

    def __setattr__(self, name, value):
        """
        Override default setting value functionality to let us send things to
        the database on updates.
        """
        super().__setattr__(name, value)
        
        # Could be picky about names of vars changing where we don't want to 
        # write out to the database
        if name in ['_dbCallback', 'online']:
            return
        
        if '_dbCallback' in self.__dict__ and self._dbCallback is not None:
            self._dbCallback(self)
    
    def __repr__(self):
        return 'Player(id: {}, user: {}, currentLegend: {}, online: {}'\
            .format(self.id, self.user.id, self.currentLegend, self.online)
            