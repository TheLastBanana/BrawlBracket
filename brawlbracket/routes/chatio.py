import datetime
from functools import wraps

from flask import session
from flask import g
from flask import abort
from flask_socketio import rooms
from flask_socketio import emit

from brawlbracket.app import socketio
from brawlbracket import usermanager as um
from brawlbracket import chatmanager as cm

print('Registering chatio routes...')

def require_chat_data(f):
    """
    Place all the data needed for chat namespace socketIO calls in g. This assumes the function will be passed a single
    argument containing JSON data, and that the value 'chatId' will be set to a valid chat id in that data.
    
    The following will be set:
    g.userId
    g.user
    g.chatId
    g.chat
    g.room
    
    An error will be emitted if any of the above values are invalid.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        g.userId = session.get('userId', None)
        
        # No userId. Could probably be handled more gracefully
        if g.userId is None:
            print('Tried to send chat message with bad info. uId: {}'
                .format(g.userId))
            return
            
        g.user = um.getUserById(g.userId)
        
        # User doesn't exist
        if g.user is None:
            print('User doesn\'t exist; message rejected')
            emit('error', {'code': 'bad-participant'},
                broadcast=False, include_self=True)
            return False
            
        data = args[0]
        g.chatId = data['chatId']
        g.chat = cm.getChat(g.chatId)
        
        # Chat doesn't exist
        if not g.chat:
            # TODO: send an error here
            return
            
        g.room = g.chat.getRoom()
        
        # User not in this chat
        if g.room not in rooms():
            # TODO: send an error here
            return
        
        return f(*args, **kwargs)
        
    return decorated_function

# A chat message was sent by a client
@socketio.on('send', namespace='/chat')
@require_chat_data
def chat_send(data):
    sentTime = datetime.datetime.now().isoformat()
    
    message = data['message']
    
    messageData = {'senderId': str(g.user.id),
                   'avatar': g.user.avatar,
                   'name': g.user.username,
                   'message': message,
                   'sentTime': sentTime}
    
    g.chat.addMessage(messageData)
    # XXX Move this to a listener
    cm._writeChatToDB(g.chat)
    
    emit('receive', {
        'messageData': messageData,
        'chatId': g.chatId
    }, broadcast=True, include_self=True, room=g.room)
    
# A user is requesting a full chat log
@socketio.on('request log', namespace='/chat')
@require_chat_data
def chat_request_log(data):
    emit('receive log', {
        'log': g.chat.log,
        'chatId': g.chatId
    }, broadcast=False, include_self=True)