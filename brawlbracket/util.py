import uuid
import os

# +-----------+
# | Util Data |
# +-----------+

# Name and path of data base
dbName = 'brawlbracketdata'
dbPath = os.path.join(os.environ['OPENSHIFT_DATA_DIR'], 'data')

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
    'koji':         'Koji',
    'ulgrim':       'Ulgrim'
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
    'koji',
    'ulgrim',
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
    'use':  'US East',
    'usw':  'US West',
    'eur':  'Europe',
    'sea':  'SE Asia',
    'aus':  'Australia',
    'bra':  'Brazil'
}
orderedRegions = list(serverRegions.items())
orderedRegions.sort(key=lambda region: region[1])

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
