'use strict';

/**
 * The admin chat multi-chat view.
 *
 * @prop {socket}   socket      - The Socket.IO socket to use for sending + receiving chat data
 * @prop {dict}     chatCache   - Cached chat logs by id
 * @prop {string}   userId      - The id of the user viewing the chatbox
 * @prop {array}    showChats   - Array of chats to display (should have id and name set)
 */
var AdminChat = React.createClass({
    render: function() {
        var socket = this.props.socket;
        var chatCache = this.props.chatCache;
        var userId = this.props.userId;
        
        return (
            <div className="row">
                <div className="col-lg-6">
                    {this.props.chatIds.map(function(chat) {
                        return (
                            <Chat
                                chatId={chat.id}
                                chatCache={chatCache}
                                userId={userId}
                                socket={socket}
                                height='300px'
                                title={'Chat with ' + chat.name}
                                key={chat.id}
                            />
                        );
                    })}
                </div>
                <div className="col-lg-6">
                
                </div>
            </div>
        );
    }
});