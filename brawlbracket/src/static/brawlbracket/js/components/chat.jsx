'use strict';

/**
 * A single message in the chatbox.
 *
 * @prop {array}    group   - The group of messages, each entry being a message JSON object
 * @prop {string}   userId  - The id of the user viewing the chatbox
 */
var ChatMessage = React.createClass({
    render: function() {
        var firstMsg = this.props.group[0];
        
        var isMe = firstMsg.senderId == this.props.userId;
        var timeDate = new Date(firstMsg.sentTime);
        // Format with only hour and minute
        var formattedTime = timeDate.toLocaleTimeString(navigator.language, {hour: '2-digit', minute: '2-digit'});
        
        return (
            <div className={'direct-chat-msg' + (isMe ? ' right' : '')}>
                <div className="direct-chat-info clearfix">
                    <span className={'direct-chat-name pull-' + (isMe ? 'right' : 'left')}>{firstMsg.name}</span>
                    <span className={'direct-chat-timestamp pull-' + (isMe ? 'left' : 'right')}>{formattedTime}</span>
                </div>
                
                <img className="direct-chat-img" src={firstMsg.avatar} alt="message user image"></img>
                <div className="direct-chat-text">
                    {this.props.group.map(function(msgData, i) {
                        // Create a paragraph for each message in the group
                        return (
                            <p key={i}>{msgData.message}</p>
                        );
                    })}
                </div>
            </div>
        );
    }
});

/**
 * A chatbox.
 *
 * @prop {string}   chatId      - The id of the chat on the server
 * @prop {socket}   socket      - The Socket.IO socket to use for sending + receiving chat data
 * @prop {dict}     chatCache   - Cached chat logs by id
 * @prop {string}   userId      - The id of the user viewing the chatbox
 * @prop {string}   height      - The height of the box
 */
var Chat = React.createClass({
    getInitialState: function() {
        return {
            log: [],
            currentChatId: null
        }
    },
    
    render: function() {
        var messages = [];
        
        if (this.state.log.length > 0) {
            var group = [this.state.log[0]];
            var i = 1;
            
            for (; i < this.state.log.length; ++i) {
                var msgData = this.state.log[i];
                var prevMsgData = group[group.length - 1];
                
                var newTime = new Date(msgData.sentTime);
                var prevTime = new Date(prevMsgData.sentTime);
                
                // If the message came soon after a previous one from the same sender, group them together
                if (newTime - prevTime < 60000 && msgData.senderId == prevMsgData.senderId) {
                    group.push(msgData);
                    
                // These will be two separate groups
                } else {
                    messages.push(
                        <ChatMessage group={group} userId={this.props.userId} key={i} />
                    );
                    
                    // Start a new group
                    group = [msgData];
                }
            }
            
            // Push the final group
            if (group.length > 0) {
                messages.push(
                    <ChatMessage group={group} userId={this.props.userId} key={i} />
                );
            }
        }
        
        return (
            <div className="box box-primary direct-chat direct-chat-primary bb-wait-for-match">
                <div className="box-header with-border">
                    <h3 className="box-title">Lobby Chat</h3>
                </div>
                <div className="box-body">
                    <div className="direct-chat-messages" style={{height: this.props.height}} ref="msgBox">
                        {messages}
                    </div>
                </div>
                <div className="box-footer">
                    <div className="input-group">
                        <input type="text" className="form-control direct-chat-input" autoComplete="off" onKeyPress={this._handleKeyPress} ref="msgInput"></input>
                        <span className="input-group-btn">
                            <button type="button" className="btn btn-primary btn-flat direct-chat-send" onClick={this._sendMessage}>Send</button>
                        </span>
                    </div>
                </div>
            </div>
        );
    },
    
    componentDidMount: function() {
        var socket = this.props.socket;
        
        socket.on('receive', this._receiveMessage);
        socket.on('receive log', this._receiveLog);
        
        this._setupLog();
    },
    
    componentWillUpdate: function() {
        var msgBox = $(this.refs.msgBox);
        
        // Only scroll down if user is already at bottom
        this.atBottom = msgBox.scrollTop() + msgBox.innerHeight() >= msgBox[0].scrollHeight;
    },
    
    componentDidUpdate: function() {
        this._setupLog();
        
        var msgBox = $(this.refs.msgBox);
        
        if (this.instant) {
            msgBox.scrollTop(msgBox[0].scrollHeight);
            
            this.instant = false;
            
        } else if (this.atBottom) {
            msgBox.animate({ scrollTop: msgBox[0].scrollHeight }, "slow");
        }
    },
    
    componentWillUnmount: function() {
        var socket = this.props.socket;
        
        socket.off('receive');
        socket.off('receive log')
    },
    
    _setupLog: function() {
        // chatId prop has changed
        if (this.state.currentChatId != this.props.chatId) {
            // Don't animate scrolling the first time
            this.instant = true;
            
            var cache = this.props.chatCache;
            
            // Already have a cached copy of this chat
            if (cache && this.props.chatId in cache) {
                this.setState({
                    log: cache[this.props.chatId].slice(),
                    currentChatId: this.props.chatId
                });
                
            // Request chat history to populate box
            } else {
                this.props.socket.emit('request log', {
                    'chatId': this.props.chatId
                });
            }
        }
    },
    
    _handleKeyPress: function(e) {
        // Pressed enter
        if (e.which == 13) {
            this._sendMessage();
        }
    },
    
    _receiveLog: function(data) {
        if (data.chatId != this.props.chatId) return;
        
        // Store when the last message was received
        if (data.log.length > 0) {
            localStorage.setItem('lastTime-' + this.props.chatId, data.log[data.log.length - 1].sentTime);
        }
        
        this.setState({
            log: data.log.slice(),
            currentChatId: this.props.chatId
        });
    },
    
    _receiveMessage: function(data) {
        if (data.chatId != this.props.chatId) return;
        var newLog = this.state.log.concat([data.messageData]);
        
        // Store when the last message was received
        localStorage.setItem('lastTime-' + this.props.chatId, data.messageData.sentTime);
        
        this.setState({
            log: newLog,
            currentChatId: this.state.currentChatId
        });
    },
    
    _sendMessage: function() {
        // Send the message and clear the textbox
        var message = this.refs.msgInput.value;
        if (message == '') return;
        
        this.props.socket.emit('send', {
            chatId: this.props.chatId,
            message: message
        });
        
        this.refs.msgInput.value = '';
    }
});