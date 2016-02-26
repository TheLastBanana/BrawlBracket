import util

class User:
    """
    A BrawlBracket user. This User persists globally across tournaments and is
    linked to a User's steam account.
    """
    
    def __init__(self, uuid, steamId, username, avatar):
        """
        User data:
         id: BrawlBracket id (uuid)
         steamId: Steam oid (int)
         username: Steam username (string)
         avatar: Avatar Url (string)
        
        Settings:
         ownedLegends: list of legends ids (string id)
         preferredServer: server id (string id)
        """
        self.id = uuid
        self.steamId = steamId
        self.username = username
        self.avatar = avatar
        self.ownedLegends = util.ownableLegendIds.copy()
        self.preferredServer = 'na'
    
    def __eq__(self, other):
        if not isinstance(other, User):
            return False
        
        if self.id == other.id:
            return True
        
        return False
    
    def __repr__(self):
        return 'User(name: {}, id: {}, sid: {}, server: {}, legends:{})' \
            .format(self.username, self.id, self.steamId, self.preferredServer,
                    self.ownedLegends)
    
    def getSettings(self):
        """
        Returns a dictionary of the User's settings for convenient conversion
        to JSON when sending through socketio.
         - Owned legends
         - Preferred server
        """
        return {'ownedLegends': self.ownedLegends,
                'preferredServer': self.preferredServer}
    
    def setSettings(self, settings):
        """
        Updates this User's settings. Will only update settings if the new
        values are valid.
        
        Return True if the settings were valid and were updated, else False.
        """
        # Bad region
        if settings['preferredServer'] not in util.serverRegions:
            return False
        
        # Bad legend
        for legend in settings['ownedLegends']:
            if legend not in util.ownableLegendIds:
                return False
        
        self.ownedLegends = settings['ownedLegends']
        return True