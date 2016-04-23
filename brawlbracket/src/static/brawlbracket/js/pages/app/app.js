// Length (in ms) to display notifications for.
var desktopNotifyLength = 3000;

// Whether the window is currently active.
var isActive = false;

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

// true if user is an admin
var adminMode;

// true if user is in the tournament as a player
var inTourney;

// Tournament socket connection
var tSocket;

// JSON data for player settings
var playerSettings;

// Admin stuff
// Admin socket connection
var aSocket;

// Page notified by each chat
var chatNotifies = {};

// Cached chat logs
var chatCache = {};

// Notification volume
var notificationVolume;

// Whether desktop notifications are enabled
var desktopNotifyEnabled;

// Chat id for this player's admin chat (player mode only)
var adminChatId;

//////////////////
// SOCKET STUFF //
//////////////////

/**
 * Connect to the server. Called when the app is first loaded.
 * @param {string}  newTourneyName - The short tourney name (Challonge URL suffix).
 * @param {string}  newUserId - The user's id.
 * @param {string}  newBasePath - The base path of the app.
 * @param {string}  startPage - The page to start on.
 * @param {boolean} isInTourney - true if the user is participating in the tourney (may be false for admins).
 * @param {boolean} isAdmin - true if the user is an admin.
 */
function brawlBracketInit(newTourneyName, newUserId, newBasePath, startPage, isInTourney, isAdmin) {
    tourneyName = newTourneyName;
    userId = newUserId;
    basePath = newBasePath;
    currentPage = startPage;
    inTourney = isInTourney;
    adminMode = isAdmin;
        
    chatSocket = io.connect(location.protocol + "//" + location.host + '/chat');
    
    chatSocket.on('receive', function(data) {
        chatNotify(data.chatId, data.messageData.senderId, false);
        
        // Desktop notify for other users' messages
        if (data.messageData.senderId != userId && !isActive) {
            desktopNotify('Message from ' + data.messageData.name,
                          data.messageData.message,
                          data.messageData.avatar);
        }
        
        // If the cache doesn't exist, we should just get the full log from the 'receive log' event anyway
        if (data.chatId in chatCache) {
            chatCache[data.chatId].push(data.messageData);
        }
    });
    
    chatSocket.on('receive log', function(data) {
        // Replace cache entirely, as this contains all chat history
        chatCache[data.chatId] = data.log;
        
        // Add notifications
        chatNotifyLog(data.chatId, data.log);
    });
    
    chatSocket.on('error', function(data) {
        handleError(data);
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
    
    // Request notification permission
    desktopNotifyEnabled = localStorage.getItem('desktopNotifyEnabled');
    if (desktopNotifyEnabled === null) desktopNotifyEnabled = true;
    if (desktopNotifyEnabled && "Notification" in window && Notification.permission != "granted") {
        Notification.requestPermission();
    }
    
    // Track whether we have window focus
    $(window).blur(function() {
        isActive = false;
    });
    
    $(window).focus(function() {
        isActive = true;
    });
    
    
    // Set up control sidebar
    // Notification olume
    notificationVolume = localStorage.getItem('notificationVolume') || 100;
    createjs.Sound.volume = notificationVolume / 100;
    
    $('#bb-volume').ionRangeSlider({
        min: 0,
        max: 100,
        from: notificationVolume,
        hide_min_max: true,
        
        onFinish: function(data) {
            notificationVolume = data.from;
            createjs.Sound.volume = notificationVolume / 100;
            localStorage.setItem('notificationVolume', notificationVolume);
        }
    });
    
    // Desktop notifications
    var notifyCheckbox = $('#bb-allow-notify');
    notifyCheckbox.checked = desktopNotifyEnabled;
    
    notifyCheckbox.change(function() {
        desktopNotifyEnabled = notifyCheckbox.is(':checked');
        localStorage.setItem('desktopNotifyEnabled', desktopNotifyEnabled);
    });
    
    defaultPage = isAdmin ? 'admin-dashboard' : 'lobby';
    
    setupTournamentSocket();
}

/**
 * Connect to the tournament socket.
 */
function setupTournamentSocket () {
    tSocket = io.connect(location.protocol + "//" + location.host + '/tournament');

    tSocket.on('error', function(data) {
        handleError(data);
    });
    
    tSocket.on('connect', function() {
        console.log('connected');
    });
    
    tSocket.on('handshake', function(data) {
        playerSettings = data.playerSettings;
        
        if (adminMode) {
            for (var i = 0; i < data.playerChats.length; ++i) {
                var chatId = data.playerChats[i];
                
                // Request chat logs so we get notifications
                chatSocket.emit('request log', {
                    'chatId': chatId
                });
                
                chatNotifies[chatId] = 'admin-chat';
            }
        }
        
        if (inTourney) {
            adminChatId = data.adminChat;
            
            // Request chat log so we get notifications
            chatSocket.emit('request log', {
                'chatId': adminChatId
            });
            
            // Tie chat id to admin contact page's notifications
            chatNotifies[adminChatId] = 'contact-admin';
        }
        
        showPage(currentPage || defaultPage, true);
    });
    
    tSocket.on('join lobby', function(data) {
        lobbyData = data.lobbyData;
        
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
    });
    
    tSocket.on('update lobby', function(data) {
        for (property in data) {
            // Maintain previous state so we can compare
            if (property == 'state') {
                lobbyData.prevState = lobbyData.state;
            }
            
            // Update specified property
            lobbyData[property] = data[property];
            
            // Lobby was previously waiting, but we're now ready to do stuff
            if (property == 'state' &&
                (lobbyData.prevState.name == 'waitingForPlayers' ||
                lobbyData.prevState.name == 'waitingForMatch') &&
                lobbyData.state.name != 'waitingForPlayers' &&
                lobbyData.state.name != 'waitingForMatch') {
                
                lobbyNotify('Your next match is ready!');
            }
            
            // Lobby was inGame and has left the state
            if (lobbyData.prevState.name == 'inGame' && lobbyData.state.name != 'inGame') {
                lobbyNotify('The game score has been reported!');
            }
            
            // Lobby has a room chosen
            if (property == 'roomNumber' && lobbyData.roomNumber) {
                lobbyNotify('The room number for your match has been set!');
            }
        }
    });
}

/**
 * Connect to the admin socket.
 */
function brawlBracketAdminInit() {
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
    if (!(tSocket in window) && !(aSocket in window)) return;

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
 * Add a notification for a page's menu option.
 * @param {string} pageName - The name of the page.
 */
function addPageNotification(pageName) {
    // Don't notify if we're already on the page
    if (pageName == currentPage) return;
    
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
 * Notify about/play sound for a chat message if necessary.
 * @param {string} chatId - The chat's id.
 * @param {string} senderId - The sender's user id.
 * @param {boolean} silent - If true, don't play sounds.
 */
function chatNotify(chatId, senderId, silent) {
    var notifyPage = chatNotifies[chatId];
    
    if (senderId != userId) {
        // Add a notification to the notify page if there is one
        if (notifyPage) {
            addPageNotification(notifyPage);
        }
        
        // Play sound if not active or if on another page
        if (!silent && (!isActive || currentPage != notifyPage)) {
            createjs.Sound.play('message');
        }
    }
}

/**
 * Notify about a lobbyData change if necessary
 * @param {string} message - The notification message.
 */
function lobbyNotify(message) {
    // Add notifications
    if (!isActive || currentPage != 'lobby') {
        if (!isActive) {
            desktopNotify('BrawlBracket update', message);
        }
        
        addPageNotification('lobby');
        createjs.Sound.play('state');
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
        
        chatNotify(chatId, log[id].senderId, true);
    }
}

/**
 * Show a desktop notification if they're enabled and the user is outside the window.
 * @param {string} title - The notification title.
 * @param {string} body - The notification body.
 * @param {string} icon - The notification icon.
 */
function desktopNotify(title, body, icon) {
    if (!desktopNotifyEnabled) return;
    if (!("Notification" in window)) return;
    if (Notification.permission != "granted") return;
    if (isActive) return;
    
    var options = {
        body: body,
        icon: icon || ''
    };
    
    var notification = new Notification(title, options);
    
    // Close after desktopNotifyLength elapses
    setTimeout(notification.close.bind(notification), desktopNotifyLength);
}

/**
 * Handle a error from the SocketIO server.
 * @param {json} error - The error data sent by the server.
 */
function handleError(error) {
    console.log('ERROR: ' + error);
    
    var message = '';
    
    switch (error.code) {
        case 'bad-participant':
            message = 'Something went wrong with your user ID. Try refreshing the page.';
            break;
            
        default:
            message = 'Something went wrong, but we\'re not sure what. Try refreshing the page.';
            break;
    }
    
    addCallout('error', 'danger', 'Error!', message);
}

$.fn.extend({
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