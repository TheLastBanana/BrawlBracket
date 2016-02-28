import uuid

class Chat:
    """
    Holds data about a chat.
    
    Attributes:
        id: Unique id.
        log: Messages in JSON format.
    """
    
    def __init__(self, **kwargs):
        """
        Create the chat with a unique id.
        """
        self.id = kwargs.get('uuid', uuid.uuid1())
        self.log = []
        
    def getRoom(self):
        """
        Get the socketIO name of the chat room.
        """
        return 'chat-{}'.format(self.id)
        
    def addMessage(self, data):
        """
        Add message data to the chat log.
        """
        self.log.append(data)