'use strict';

/**
 * The admin chat multi-chat view.
 *
 * @prop {socket}   socket          - The Socket.IO socket to use for sending + receiving chat data
 * @prop {dict}     chatCache       - Cached chat logs by id
 * @prop {string}   userId          - The id of the user viewing the chatbox
 * @prop {array}    chats           - Array of chats to display (should have id and name set)
 * @prop {function} removeCallback  - Function called when a chat is removed. It will be passed the chatId
 */
var AdminChat = React.createClass({
    render: function() {
        var socket = this.props.socket;
        var chatCache = this.props.chatCache;
        var userId = this.props.userId;
        var removeCallback = this._chatRemoved;
        
        // Generate chat boxes
        var childrenChats = this.props.chats.map(function(chat) {
            return (
                <Chat
                    chatId={chat.id}
                    chatCache={chatCache}
                    userId={userId}
                    socket={socket}
                    height='300px'
                    title={'Chat with ' + chat.name}
                    removable={true}
                    removeCallback={removeCallback}
                    key={chat.id}
                />
            );
        });
        
        // Split into two columns
        var columnA = [];
        var columnB = [];
        for (var i = 0; i < childrenChats.length; i += 2) {
            columnA.push(childrenChats[i]);
            childrenChats[i+1] && columnB.push(childrenChats[i+1]);
        }
        
        return (
            <div className="row">
                <div className="col-lg-6">
                    {columnA}
                </div>
                <div className="col-lg-6">
                    {columnB}
                </div>
            </div>
        );
    },
    
    _chatRemoved: function(chatId) {
        if (this.props.removeCallback) {
            this.props.removeCallback(chatId);
        }
    }
});