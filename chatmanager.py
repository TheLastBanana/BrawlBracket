import chat

_chats = {}

def createChat(tourneyId):
    """
    Create a chat.
    
    Returns the Chat.
    """
    chat = chat.Chat()
    
    _chats.append(chat)
        
    return chat
    
def getChat(id):
    """
    Get a chat by uuid.
    
    Returns the Chat if it exists.
    Returns None otherwise.
    """
    for chat in _chats:
        if chat.id == id:
            return chat
    
    return None