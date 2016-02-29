from brawlbracket import chat

_chats = []

def createChat():
    """
    Create a chat.
    
    Returns the Chat.
    """
    newChat = chat.Chat()
    
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
    
    return None