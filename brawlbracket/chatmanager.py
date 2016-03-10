import json

from brawlbracket import chat
from brawlbracket import db_wrapper
from brawlbracket import util

_chats = []

_db = None

def createChat():
    """
    Create a chat.
    
    Returns the Chat.
    """
    newChat = chat.Chat()
    
    _writeChatToDB(newChat)
    
    _chats.append(newChat)
    
    return newChat
    
def getChat(id):
    """
    Get a chat by uuid.
    
    Returns the Chat if it exists.
    Returns None otherwise.
    """
    for c in _chats:
        if c.id == id:
            return c
            
    c = _getChatFromDB(id)
    if c is not None:
        _chats.append(c)
        return c
    
    return None

def _getChatFromDB(id):
    """
    Gets a chat from the database by steamId.
    
    Returns chat if chat was in database
    Returns None otherwise
    """
    if _db is None:
        _initDB()
    
    # Quick function that returns a string surrounded by quotes
    q = lambda x: '\'{}\''.format(x)
    
    rows = _db.select_values('chats', ['*'], [q('id = {}'.format(id))])
    
    if rows:
        chatData = rows[0]
        print('Making chat from: ', chatData)
        id = chatData[0]
        log = json.loads(chatData[1])
        
        newChat = chat.Chat(id)
        newChat.log = log
        
        return newChat
    else:
        return None

def _writeChatToDB(c):
    """
    Serializes a chat and then inserts it into the chat table of the database.
    """
    if _db is None:
        _initDB()
    
    chatData = (
        c.id,
        json.dumps(c.log)
        )
    print('Writing chats with: ', chatData)
    _db.insert_values('chats', [chatData])
        
def _initDB():
    print('----INIT CHAT DATABASE----')
    # Need to global because _db is not local to this context
    global _db
    _db = db_wrapper.DBWrapper(util.dbName, filepath=util.dbPath)
    
    # Make chats table
    if not _db.table_exists('chats'):
        fieldNames = [
            'id',
            'log'
            ]
        fieldTypes = [
            'UUID',
            'TEXT'
            ]
            
        _db.create_table('chats', fieldNames, fieldTypes, 'id')
