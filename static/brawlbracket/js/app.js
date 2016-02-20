// Chat socket connection
var chatSocket;

// JSON data for lobby
var lobbyData;

// Current page in the app
var currentPage;

// Default page within the app
var defaultPage;

// Challonge short name for the tourney
var tourneyName;

// Id of current user
var userId;

// Participant stuff
// Participant socket connection
var pSocket;

// JSON data for player settings
var playerSettings;

// Admin stuff
// Admin socket connection
var aSocket;

// Page notified by each chat
var chatNotifies = {};

// Cached chat logs
var chatCache = {};

//////////////////
// SOCKET STUFF //
//////////////////

/**
 * Connect to the server. Called when the app is first loaded.
 * @param {string} newTourneyName - The short tourney name (Challonge URL suffix).
 * @param {string} newUserId - The user's id.
 * @param {string} newBasePath - The base path of the app.
 * @param {string} startPage - The page to start on.
 */
function brawlBracketInit(newTourneyName, newUserId, newBasePath, startPage) {
    tourneyName = newTourneyName;
    userId = newUserId;
    basePath = newBasePath;
    currentPage = startPage;
    
    chatSocket = io.connect(window.location.origin + '/chat');
    
    chatSocket.on('receive', function(data) {
        console.log('receive', data);
        
        chatNotify(data.chatId, data.messageData.senderId);
        
        // Play sound for other users' messages
        if (data.messageData.senderId != userId) {
            createjs.Sound.play('message');
        }
        
        // If the cache doesn't exist, we should just get the full log from the 'receive log' event anyway
        if (data.chatId in chatCache) {
            chatCache[data.chatId].push(data.messageData);
        }
        
        // If this page includes the chat box, update it
        var chatBox = $('.direct-chat[chatId=' + data.chatId + ']');
        if (chatBox.length == 0) return;
        addChatMessage(chatBox, data.messageData, false);
    });
    
    chatSocket.on('receive log', function(data) {
        console.log('receive log', data);
        
        // Replace cache entirely, as this contains all chat history
        chatCache[data.chatId] = data.log;
        
        // Add notifications
        chatNotifyLog(data.chatId, data.log);
        
        // If this page includes the chat box, update it
        var chatBox = $('.direct-chat[chatId=' + data.chatId + ']');
        if (chatBox.length == 0) return;
        
        addAllChatMessages(chatBox, data.log);
    });

    var menuOptions = $('.bb-menu-option');
    
    // Add notification label to menu options
    menuOptions.each(function() {
        var $this = $(this);
        var label = $('<span class="notify-label label label-primary pull-right"></span>');
        $this.find('a').append(label);
        
        label.data('notifyCount', 0);
    });
    
    // Add functionality to menu options
    menuOptions.on('click', function(event) {
        showPage($(this).attr('page'));
        
        return false;
    });

    // When we change the URL, update the page
    window.onpopstate = function(event) {
        if (event.state) {
            showPage(event.state.page, true);
        }
    }
    
    // Create sounds
    createjs.Sound.alternateExtensions = ['mp3'];
    createjs.Sound.registerSound('/static/brawlbracket/sfx/message.ogg', 'message');
    createjs.Sound.registerSound('/static/brawlbracket/sfx/state.ogg', 'state');
}

/**
 * Connect to the participant socket.
 */
function brawlBracketParticipantInit() {
    pSocket = io.connect(window.location.origin + '/participant');
    defaultPage = 'lobby';

    pSocket.on('error', function() {
        $('.content-wrapper').load(getContentURL('lobby-error'));
    });
    
    pSocket.on('connect', function() {
        console.log('connected');
    });
    
    pSocket.on('join lobby', function(data) {
        lobbyData = data.lobbyData;
        playerSettings = data.playerSettings;
        
        // Request chat log so we get notifications
        chatSocket.emit('request log', {
            'chatId': lobbyData.chatId
        });
        
        // Tie chat id to lobby page's notifications
        chatNotifies[lobbyData.chatId] = 'lobby';
        
        // Set empty previous state
        lobbyData.prevState = {
            'name': null
        };
        
        showPage(currentPage || defaultPage, true);
    });
    
    pSocket.on('update lobby', function(data) {
        // Maintain previous state so we can compare
        if (data.property == 'state') {
            lobbyData.prevState = lobbyData.state;
        }
        
        // Update specified property
        lobbyData[data.property] = data.value;
        
        // Add notifications when state changes
        if (currentPage != 'lobby' && data.property == 'state') {
            // Lobby was previously waiting, but we're now ready to do stuff
            if ((lobbyData.prevState.name == 'waitingForPlayers' ||
                lobbyData.prevState.name == 'waitingForMatch') &&
                lobbyData.state.name != 'waitingForPlayers' &&
                lobbyData.state.name != 'waitingForMatch') {
                
                addPageNotification('lobby');
                createjs.Sound.play('state');
            }
            
            // TODO: Add notifications for room chosen and score changed
        }
    });
}

/**
 * Connect to the admin socket.
 */
function brawlBracketAdminInit() {
    defaultPage = 'admin-dashboard';
    showPage(currentPage || defaultPage, true);
}


//////////////////////
// HELPER FUNCTIONS //
//////////////////////

/**
 * Get a content page's URL including tourney and participant data.
 * @param {string} pageName - The name of the page to load. Should exist at
 *   /app-content/<pageName>/<tourneyName>
 */
function getContentURL(pageName) {
    return '/app-content/' + pageName + '/' + tourneyName;
}

/**
 * Create a participant status DOM element.
 * @param {boolean} ready - If true, the status is "Ready," else "Not Ready."
 */
function createStatus(ready) {
    color = ready ? 'green' : 'yellow';
    status = ready ? 'Ready' : 'Not Ready';
    
    return $('<h2 class="description-status text-' + color + '">' + status + '</h2>');
}

/**
 * Create a chat message DOM element.
 * @param {string} name - The name of the sender.
 * @param {string} time - Date string representing the time the message was sent.
 * @param {string} avatar - The sender's avatar.
 * @param {string} text - The text of the message.
 * @param {boolean} right - Should be true for the current user's messages and false for others.
 */
function createChatMessage(name, time, avatar, text, right) {
    var messageRoot = $('<div class="direct-chat-msg"></div>');
    
    if (right) messageRoot.addClass('right');
    
    var info = $('<div class="direct-chat-info clearfix"></div>');
    
    var timeDate = new Date(time);
    var formattedTime = timeDate.toLocaleTimeString();
    var msgTime = $('<span class="direct-chat-timestamp"></span>').text(formattedTime);
    
    var msgName = $('<span class="direct-chat-name"></span>').text(name);
    
    // Align name with avatar and put timestamp on the other side
    if (right) {
        msgName.addClass('pull-right');
        msgTime.addClass('pull-left');
    }
    else {
        msgName.addClass('pull-left');
        msgTime.addClass('pull-right');
    }
    
    info.append(msgName);
    info.append(msgTime);
    messageRoot.append(info);
    
    messageRoot.append($('<img class="direct-chat-img">').attr('src', avatar));
    messageRoot.append($('<div class="direct-chat-text"></div>').text(text));
    
    return messageRoot;
}

/**
 * Left-pad a string with a given character.
 * @param {string} str - The string.
 * @param {number} count - The number of characters to pad to.
 * @param {string} padChar - The character to use for padding.
 */
function padString(str, count, padChar) {
    var pad = Array(count + 1).join(padChar);
    return pad.substring(0, pad.length - str.length) + str;
}

/**
 * Get a string representing the time since a timer began.
 * @param {string} isoTime - Time in ISO 8601 format.
 */
function getTimerString(isoTime) {
    var timeDiff = new Date(new Date() - new Date(isoTime));
    var minStr = "" + timeDiff.getMinutes();
    var secStr = "" + timeDiff.getSeconds();
    
    return padString(minStr, 2, '0') + ":" + padString(secStr, 2, '0');
}

//////////////////
// UI FUNCTIONS //
//////////////////

/**
 * Show an app page, update the menu, and update the URL.
 * @param {string} pageName - The name of the page (see getContentURL()).
 * @param {boolean} replace - If true, replace the page rather than pushing.
 */
function showPage(pageName, replace) {
    if (!(pSocket in window) && !(aSocket in window)) return;

    replace = replace || false;
    
    // Show the active menu option
    $('.bb-menu-option').removeClass('active');
    $('.bb-menu-option[page="' + pageName + '"]').addClass('active');
    
    // Load page content
    var wrapper = $('.content-wrapper');
    wrapper.find('.content').trigger('destroy');
    wrapper.addClass('not-ready');
    wrapper.load(getContentURL(pageName), function() {
        wrapper.removeClass('not-ready');
    });
    
    // Update page
    currentPage = pageName;
    
    // Update browser history
    var state = {
        'page': currentPage
    };
    var page = basePath + pageName + '/';
    
    if (replace) {
        window.history.replaceState(state, null, page);
    } else {
        window.history.pushState(state, null, page);
    }
    
    clearPageNotifications(pageName);
}

/**
 * Add a callout at the top of the app. If a callout with this id exists, replace it.
 * @param {string} id - Unique identifier for this callout (suffix to "bb-callout-").
 * @param {string} type - One of {danger, info, warning, success}.
 * @param {string} title - Callout title (optional).
 * @param {string} message - Callout message (optional).
 * @param {string} animation - 'in'/'inOut'/'none'. Optional.
 * @returns {jQuery object} The callout object.
 */
function addCallout(id, type, title, message, animation) {
    removeCallout(id);
    
    var callout = $('<div class="callout callout-' + type + '" id="' + id + '"></div>');
    if (title) callout.append('<h4>' + title + '</h4>');
    if (message) callout.append('<p>' + message + '</p>');
    
    $('.callout-container').prepend(callout);
    
    if (animation) {
        switch (animation) {
            case 'in':
                callout.hide().slideDown();
                break;
                
            case 'inOut':
                callout.hide().slideDown().delay(3000).slideUp();
                break;
                
            case 'none':
            default:
                break;
        }
    }
    
    return callout;
}

/**
 * Remove a callout from the top of the app.
 * @param {string} id - Unique identifier for this callout (suffix to "bb-callout-").
 */
function removeCallout(id) {
    $('#bb-callout-' + id).remove();
}

/**
 * Receive a chat message.
 * @param {jQuery object} chatBox - The outermost element of the chat box.
 * @param {json} msgData - Message JSON data.
 *     @param {string} msgData.name - The name of the sender.
 *     @param {string} msgData.sentTime - Date string representing the time the message was sent.
 *     @param {string} msgData.avatar - The sender's avatar.
 *     @param {string} msgData.message - The text of the message.
 *     @param {string} msgData.senderId - The Challonge participant id of the sender.
 * @param {string} msgData - The string.
 */
function addChatMessage(chatBox, msgData, instant) {
    var msg = createChatMessage(msgData.name, msgData.sentTime, msgData.avatar,
                                msgData.message, msgData.senderId == userId);
                                
    var msgBox = chatBox.find('.direct-chat-messages');
    
    // Only scroll down if user is already at bottom
    var atBottom = msgBox.scrollTop() + msgBox.innerHeight() >= msgBox[0].scrollHeight;
    
    msg.appendTo(msgBox);
    
    // Do this after append so we can get the actual height
    if (atBottom && !instant) {
        msgBox.animate({ scrollTop: msgBox[0].scrollHeight }, "slow");
    }
    
    localStorage.setItem('lastTime-' + chatBox.attr('chatId'), msgData.sentTime);
}

/**
 * Send a message from a chat box and empty the chat box.
 * Does nothing if the box is empty.
 * @param {jQuery object} chatBox - The outermost element of the chat box.
 */
function sendChat(chatBox) {
    var input = chatBox.find('.direct-chat-input');
    
    var message = input.val();
    if (message == '') return;
    
    chatSocket.emit('send', {
        'chatId': chatBox.attr('chatId'),
        'message': message
    });
    
    input.val('');
}

/**
 * Add a notification for a page's menu option.
 * @param {string} pageName - The name of the page.
 */
function addPageNotification(pageName) {
    $('.bb-menu-option[page="' + pageName + '"] .notify-label').addNotification();
}

/**
 * Clean notifications for a page's menu option.
 * @param {string} pageName - The name of the page.
 */
function clearPageNotifications(pageName) {
    $('.bb-menu-option[page="' + pageName + '"] .notify-label').clearNotifications();
}

/**
 * Notify about a chat message if necessary.
 * @param {string} chatId - The chat's id.
 * @param {string} senderId - The sender's user id.
 */
function chatNotify(chatId, senderId) {
    var notifyPage = chatNotifies[chatId];
    
    // Chat message from another page, so add a notification
    if (notifyPage && currentPage != notifyPage && senderId != userId) {
        addPageNotification(notifyPage);
    }
}

/**
 * Notify about chat messages from a log if necessary.
 * @param {string} chatId - The chat's id.
 * @param {array} log - The array of messages.
 */
function chatNotifyLog(chatId, log) {
    var lastTime = localStorage.getItem('lastTime-' + chatId);
    var lastDate = new Date(lastTime);
    
    for (id in log) {
        // This came before or on last message date, so don't notify
        var messageDate = new Date(log[id].sentTime);
        if (messageDate <= lastDate) continue;
        
        chatNotify(chatId, log[id].senderId);
    }
}

/**
 * Add all the messages in a chat log to a chat box.
 * @param {jQuery object} chatBox - The chatbox to populate.
 * @param {array} log - The chat log to use.
 */
function addAllChatMessages(chatBox, log) {
    var msgBox = chatBox.find('.direct-chat-messages');
        
    msgBox.empty();
    
    for (id in log) {
        addChatMessage(chatBox, log[id], true);
    }
    
    // Skip to bottom
    msgBox.scrollTop(msgBox[0].scrollHeight);
}

$.fn.extend({
    toggleDisabled: function() {
        return $(this).each(function() {
            if ($(this).hasClass('disabled')) {
                $(this).removeClass('disabled');
            }
            else {
                $(this).addClass('disabled');
            }
        });
    },
    
    setUpChatBox: function(chatId) {
        return $(this).each(function() {
            var chatBox = $(this);
            
            // Set chat id so we know which chat this links to
            chatBox.attr('chatId', chatId);
            
            // Make send button send
            chatBox.find('.direct-chat-send').on('click', function(event) {
                sendChat(chatBox);
                
                return false;
            });
            
            // Make enter button send
            chatBox.find('.direct-chat-input').keypress(function(e) {
                if (e.which == 13) {
                    sendChat(chatBox);
                }
            });
            
            if (chatId in chatCache) {
                var cache = chatCache[chatId];
                
                // Fill chat from cache
                addAllChatMessages(chatBox, cache);
        
                // Add notifications
                chatNotifyLog(chatId, cache);
                
            } else {
                // Request chat history to populate box
                chatSocket.emit('request log', {
                    'chatId': chatId
                });
            }
        });
    },
    
    clearNotifications: function() {
        return $(this).each(function() {
            var $this = $(this);
            
            // Set count to 0
            $this.data('notifyCount', 0);
            $this.updateNotificationCount(0);
        });
    },
    
    addNotification: function() {
        return $(this).each(function() {
            var $this = $(this);
            var count = $this.data('notifyCount');
            ++count;
            
            // Add 1 to count
            $this.data('notifyCount', count);
            $this.updateNotificationCount(count);
        });
    },
    
    updateNotificationCount: function(newCount) {
        return $(this).each(function() {
            // Display empty string if count is 0
            $(this).text(newCount || '');
        });
    }
});