'use strict';

var ChatMessage = React.createClass({
    render: function() {
        var isMe = this.props.data.senderId == userId;
        var timeDate = new Date(this.props.data.sentTime);
        var formattedTime = timeDate.toLocaleTimeString();
        
        return (
            <div className={'direct-chat-msg' + (isMe ? ' right' : '')}>
                <div className="direct-chat-info clearfix">
                    <span className={'direct-chat-name pull-' + (isMe ? 'right' : 'left')}>{this.props.data.name}</span>
                    <span className={'direct-chat-timestamp pull-' + (isMe ? 'left' : 'right')}>{formattedTime}</span>
                </div>
                
                <img className="direct-chat-img" src={this.props.data.avatar} alt="message user image"></img>
                <div className="direct-chat-text">{this.props.data.message}</div>
            </div>
        );
    }
});

var Chat = React.createClass({
    getInitialState: function() {
        return {
            log: []
        }
    },
    
    render: function() {
        var messages = [];
        for (var i = 0; i < this.state.log.length; ++i) {
            var msgData = this.state.log[i];
            messages.push(
                <ChatMessage data={msgData} key={i} />
            );
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
                        <input type="text" placeholder="Type Message ..." className="form-control direct-chat-input" autoComplete="off" onKeyPress={this._handleKeyPress} ref="msgInput"></input>
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
        
        // Don't animate scrolling the first time
        this.instant = true;
        
        var cache = this.props.chatCache;
        
        // Already have a cached copy of this chat
        if (cache && this.props.chatId in cache) {
            this.setState({
                log: cache[this.props.chatId].slice()
            });
            
        // Request chat history to populate box
        } else {
            socket.emit('request log', {
                'chatId': this.props.chatId
            });
        }
    },
    
    componentWillUpdate: function() {
        var msgBox = $(this.refs.msgBox);
        
        // Only scroll down if user is already at bottom
        this.atBottom = msgBox.scrollTop() + msgBox.innerHeight() >= msgBox[0].scrollHeight;
    },
    
    componentDidUpdate: function() {
        var msgBox = $(this.refs.msgBox);
        
        // Do this after append so we can get the actual height
        if (this.instant) {
            msgBox.scrollTop(msgBox[0].scrollHeight);
            
            this.instant = false;
            
        } else if (this.atBottom) {
            msgBox.animate({ scrollTop: msgBox[0].scrollHeight }, "slow");
        }
    },
    
    componentWillUnmount: function() {
        socket.off('receive');
        socket.off('receive log')
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
            log: data.log.slice()
        });
    },
    
    _receiveMessage: function(data) {
        if (data.chatId != this.props.chatId) return;
        var newLog = this.state.log.concat([data.messageData]);
        
        // Store when the last message was received
        localStorage.setItem('lastTime-' + this.props.chatId, data.messageData.sentTime);
        
        this.setState({
            log: newLog
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

function createChat(container, socket, chatId, chatCache, height) {
    ReactDOM.render(
        <Chat height={height} socket={socket} chatId={chatId} chatCache={chatCache} />,
        container
    );
}