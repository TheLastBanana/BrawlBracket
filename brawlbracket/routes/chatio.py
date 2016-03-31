import datetime

from flask import session
from flask_socketio import rooms
from flask_socketio import emit

from brawlbracket.app import socketio
from brawlbracket import usermanager as um
from brawlbracket import chatmanager as cm

print('Registering chatio routes...')

# A chat message was sent by a client
@socketio.on('send', namespace='/chat')
def chat_send(data):
    userId = session.get('userId', None)
    
    # No tourneyId, userId. Could probably be handled more gracefully
    if userId is None:
        print('Tried to send chat message with bad info. uId: {}'
            .format(userId))
        return
    
    user = um.getUserById(userId)
    
    # User doesn't exist
    if user is None:
        print('User doesn\'t exist; message rejected')
        emit('error', {'code': 'bad-participant'},
            broadcast=False, include_self=True)
        return False
        
    sentTime = datetime.datetime.now().isoformat()
    
    chatId = data['chatId']
    message = data['message']
    
    chat = cm.getChat(chatId)
    if not chat:
        return
        
    room = chat.getRoom()
    
    # User not in this chat
    if room not in rooms():
        return
    
    messageData = {'senderId': str(user.id),
                   'avatar': user.avatar,
                   'name': user.username,
                   'message': message,
                   'sentTime': sentTime}
    
    chat.addMessage(messageData)
    # XXX Move this to a listener
    cm._writeChatToDB(chat)
    
    emit('receive', {
        'messageData': messageData,
        'chatId': chatId
    }, broadcast=True, include_self=True, room=room)
    
# A user is requesting a full chat log
@socketio.on('request log', namespace='/chat')
def chat_request_log(data):
    chatId = data['chatId']
    
    chat = cm.getChat(chatId)
    
    # TODO: Maybe handle this a bit more gracefully
    if not chat:
        return
        
    room = chat.getRoom()
    
    # User not in this chat
    if room not in rooms():
        return
    
    emit('receive log', {
        'log': chat.log,
        'chatId': chatId
    }, broadcast=False, include_self=True)