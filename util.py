import uuid

# +-----------+
# | Util Data |
# +-----------+

# Mapping from legend internal name to full name
legendData = {
    'random':       'Random',
    'bodvar':       'Bödvar',
    'cassidy':      'Cassidy',
    'orion':        'Orion',
    'vraxx':        'Lord Vraxx',
    'gnash':        'Gnash',
    'nai':          'Nai',
    'hattori':      'Hattori',
    'roland':       'Sir Roland',
    'scarlet':      'Scarlet',
    'thatch':       'Thatch',
    'ada':          'Ada',
    'sentinel':     'Sentinel',
    'lucien':       'Lucien',
    'teros':        'Teros',
    'brynn':        'Brynn',
    'asuri':        'Asuri',
    'barraza':      'Barraza',
    'ember':        'Ember',
    'azoth':        'Azoth',
}

# Order they appear in-game, with random always last
legendOrder = [
    'bodvar',
    'cassidy',
    'orion',
    'vraxx',
    'gnash',
    'nai',
    'hattori',
    'roland',
    'scarlet',
    'thatch',
    'ada',
    'sentinel',
    'lucien',
    'teros',
    'brynn',
    'asuri',
    'barraza',
    'ember',
    'azoth',
    'random'
]
orderedLegends = [(id, legendData[id]) for id in legendOrder]
ownableLegendIds = legendOrder[:-1]

# Mapping from realm id to (formatted name, internal name)
realmData = {
    'random':           'Random',
    'brawlhaven':       'Brawlhaven',
    'grumpy':           'Grumpy Temple',
    'twilight':         'Twilight Grove',
    'kings':            'Kings Pass',
    'thunder':          'Thundergard Stadium',
    'titan':            'Titan\'s End',
    'keep':             'Blackguard Keep',
    'enigma':           'The Enigma',
    'mammoth':          'Mammoth Fortress',
    'hall':             'Great Hall',
    'falls':            'Shipwreck Falls',
    'big-hall':         'Big Great Hall',
    'big-kings':        'Big Kings Pass',
    'big-thunder':      'Big Thundergard Stadium',
    'big-titan':        'Big Titan\'s End',
    'big-twilight':     'Big Twilight Grove',
    'bombsketball':     'Bombsketball',
    'brawlball':        'Brawlball',
    'wally':            'Wally',
    'short':            'Short Side',
    'pillars':          'Pillars'
}

# Realms used by ESL 1v1 tourneys
eslRealms = [
    'twilight',
    'kings',
    'thunder',
    'keep',
    'mammoth',
    'hall',
    'falls'
]
orderedRealms = [realmData[id] for id in eslRealms]

# Valid server regions
serverRegions = {
    'na':   'North America',
    'eu':   'Europe',
    'sea':  'Southeast Asia'
}

# +--------------+
# | Util classes |
# +--------------+

class KeySingleton(type):
    """
    A form of singleton where the singleton is based on a defining attribute.
    Only one instance for each defining attribute and class combination will be created.
    Uses the first variable as the key. If something else is needed as the key then
    KeySingleton must be subclassed.
    """
    instances = {}
    def __call__(cls, key, *args, **kw):
        if cls.__name__ not in cls.instances:
            cls.instances[cls.__name__] = {key: super(KeySingleton, cls).__call__(key, *args, **kw)}
        elif key not in cls.instances[cls.__name__]:
            cls.instances[cls.__name__][key] = super(KeySingleton, cls).__call__(key, *args, **kw)
        return cls.instances[cls.__name__][key]

        
class User:
    """
    Represents a user. This could be a participant in a tournament or a player
    on a team in a tournament. It's up to calling code to know which tournament
    this user belongs to.
    
    NOTE: If the data in this User changes please update refreshParticipantX
    as appropriate.
    
    Attributes:
        userId: Unique, BrawlBracket-internal id.
        participantId: the partiicpant id for this user.
        isAdmin:  is this user a tournament admin.
    """
    
    def __init__(self, participantId=None, isAdmin=False):
        """
        Initialize the User.
        
        pariticpantId: this user's id in the tournament.
        isAdmin: is this user a tournament admin.
        
        NOTE: participantId or isAdmin MUST be set. Both can be set, but at
        least one must be.
        """
        if participantId is None and not isAdmin:
            raise ValueError("Bad user init, not pId and not admin.")
        
        # Want to make sure we're always using ints
        if not isinstance(participantId, int):
            raise ValueError("Bad user init, pId wasn't int ({})."
                .format(type(participantId)))
        
        # Generate our own uuid
        self.userId = uuid.uuid4()
        
        self.pariticipantId = participantId
        self.isAdmin = isAdmin
    
    def __eq__(self, other):
        """
        Are two Users equal.
        
        This is a very wary way of doing this but I'm scared of the possibility
        of users matching only part way.
        """
        if not isinstance(other, User):
            return False
        
        # Want to make sure we're always using ints
        # This is kind of out of place but it'll help catch bugs early
        if not isinstance(other.participantId, int) or \
                isinstance(self.participantId, int):
            raise ValueError("Bad eq, pId wasn't int ({}, {})."
                .format(type(self.participantId), type(other.participantId))
            
        uIdEq = (self.userId == other.userId)
        adminEq = (self.isAdmin == other.isAdmin)
        
        pIdEq = False
        # Using is for None..
        if self.participantId is None and other.participantId is None:
            pIdEq = True
        elif self.participantId == other.participantId:
            pIdEq = True
        
        return uIdEq and pIdEq and adminIdEq
