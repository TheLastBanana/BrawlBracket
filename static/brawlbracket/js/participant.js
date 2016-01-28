// Participant socket connection
var pSocket;

// JSON data for lobby
var lobbyData;

// Lobby timer interval so it can be cleared/checked later
var lobbyTimer;

// Current page in the app
var currentPage;

// Challonge short name for the tourney
var tourneyName;

// Challonge participant id of current user
var participantId;

// Functions to call after a page is loaded
var pageSetup = {
    'lobby': function() {
        updateLobbyUI();
        
        // Set up chat
        var lobbyMsgBox = $('#bb-lobby-chat-message');
        $('#bb-lobby-chat-send').on('click', function(event) {
            sendChat('lobby chat', lobbyMsgBox);
            
            return false;
        });
        $('#bb-lobby-chat-message').keypress(function(e) {
            // Enter pressed in chat message box
            if (e.which == 13) {
                sendChat('lobby chat', lobbyMsgBox);
            }
        });
        
        currentPage = 'lobby';
        
        // DEBUG
        //$('#bb-picker-content').load('/app-content/lobby-realms');
    }
};

// Functions to update UI from lobbyData
var lobbyUIFunctions = {
    'participants': function () {
        var participants = lobbyData.participants;
        
        if (lobbyData.state.name == 'waitingForMatch') return;
        if (participants.length != 2) return;
        
        // Add Report Win button functionality
        $('#bb-par1-report-win').on('click', function(event) {
            reportWin(lobbyData.participants[0].id);
            
            return false;
        });
        
        $('#bb-par2-report-win').on('click', function(event) {
            reportWin(lobbyData.participants[1].id);
            
            return false;
        });
        
        // Participant info
        $('#bb-par1-name').text(participants[0].name + ' ').append('<sup>(' + participants[0].seed + ')</sup>');
        $('#bb-par2-name').text(participants[1].name + ' ').append('<sup>(' + participants[1].seed + ')</sup>');
        $('#bb-par1-avatar').attr('src', participants[0].avatar);
        $('#bb-par2-avatar').attr('src', participants[1].avatar);
        $('#bb-score').text(participants[0].wins + '-' + participants[1].wins);
        
        // Show "report win" buttons when game is being played
        if (lobbyData.state.name == 'inGame') {
            $('#bb-par1-description').append(createReportWinButton(lobbyData.participants[0].id));
            $('#bb-par2-description').append(createReportWinButton(lobbyData.participants[1].id));
        }
        // Update participant status
        else {
            $('#bb-par1-description').append(createStatus(participants[0].ready));
            $('#bb-par2-description').append(createStatus(participants[1].ready));
        }
    },
    
    'players': function () {
        var players = lobbyData.players;
        
        if (lobbyData.state.name == 'waitingForMatch') return;
        if (players.length != 2) return;
        
        // Player info
        $('#bb-pla1-name').text(lobbyData.players[0].name);
        $('#bb-pla2-name').text(lobbyData.players[1].name);
        
        var legendBase = '/static/brawlbracket/img/legends-small/'
        $('#bb-pla1-legend').attr('src', legendBase + lobbyData.players[0].legend + '.png');
        $('#bb-pla2-legend').attr('src', legendBase + lobbyData.players[1].legend + '.png');
        
        $('#bb-pla1-status').attr('data-original-title', lobbyData.players[0].status);
        $('#bb-pla2-status').attr('data-original-title', lobbyData.players[1].status);
    },
    
    'state': function () {
        switch (lobbyData.state.name) {
            case 'waitingForMatch':
                // Disable everything and put spinners on them.
                $('.bb-wait-for-match').append(
                    $('<div class="overlay"><i class="fa fa-circle-o-notch fa-spin"></i></div>')
                );
                
                // Add a notice at the top about the prerequisite match.
                var msg = 'You\'ll be notified as soon as match <strong>#' + lobbyData.state.matchNumber +
                          '</strong> (<strong>' + lobbyData.state.participantNames[0] +
                          '</strong> vs <strong>' + lobbyData.state.participantNames[1] + '</strong>) finishes.';
                
                addCallout('state', 'warning',
                           'Your opponent hasn\'t finished their game yet!',
                           msg);
                           
                break;
                
            case 'waitingForPlayer':
                // Add a notice about the player missing.
                addCallout('state', 'warning',
                           'Your opponent hasn\'t finished their game yet!',
                           'You\'ll be notified as soon as they\'re ready.');
                break;
                
            case 'inGame':
                // Replace status with "report win" buttons
                lobbyUIFunctions.participants();
                break;
        }
        
        switch (lobbyData.prevState.name) {
            case 'inGame':
                // Replace "report win" buttons with status
                lobbyUIFunctions.participants();
                break;
        }
    },
    
    'chatlog': function () {
        if (lobbyData.state.name == 'waitingForMatch') return;
        
        var msgBox = $('#bb-lobby-chat-messages');
        
        // Create messages
        for (id in lobbyData.chatlog) {
            var msgData = lobbyData.chatlog[id];
            onLobbyChat(msgBox, msgData, true);
        }
    },
    
    'realmBans': function () {
        if (lobbyData.state.name == 'waitingForMatch') return;
        
    },
    
    'bestOf': function() {
        if (lobbyData.state.name == 'waitingForMatch') return;
        
        $('#bb-best-of').text('BEST OF ' + lobbyData.bestOf);
    },
    
    'startTime': function() {
        if (lobbyData.state.name == 'waitingForMatch') return;
        
        updateLobbyTimer();
        if (!lobbyTimer) setInterval(updateLobbyTimer, 1000);
    },
    
    'roomNumber': function () {
        if (lobbyData.state.name == 'waitingForMatch') return;
        
        $('#bb-room-number').text(lobbyData.roomNumber);
    },
    
    'currentRealm': function () {
        if (lobbyData.state.name == 'waitingForMatch') return;
        
        $('#bb-current-realm').text(lobbyData.currentRealm);
    },
    
    'challongeId': function () {
        var matchName = 'Match #' + lobbyData.challongeId;
        $('.bb-page-name').text(matchName);
    }
};

$(window).on('beforeunload', function() {
    pSocket.close();
});


//////////////////
// SOCKET STUFF //
//////////////////

/**
 * Connect to the server. Called when the app is first loaded.
 * @param {string} newTourneyName - The short tourney name (Challonge URL suffix).
 * @param {string} newParticipantId - The participant's Challonge id.
 */
function brawlBracketInit(newTourneyName, newParticipantId) {
    tourneyName = newTourneyName;
    participantId = newParticipantId;
    
    pSocket = io.connect(window.location.origin + '/participant');

    pSocket.on('error', function() {
        $('.content-wrapper').load(getContentURL('lobby-error'));
    });
    
    pSocket.on('connect', function() {
        console.log('connected');
    });
    
    pSocket.on('join lobby', function(newLobbyData) {
        lobbyData = newLobbyData;
        
        // Set empty previous state
        lobbyData.prevState = {
            'name': null
        };
        
        // Get menu option/page from URL hash
        hashPage = window.location.hash.substring(1);
        
        if ($('.bb-menu-option[page="' + hashPage + '"]').length > 0) {
            showPage(hashPage);
        }
        else {
            showPage('lobby');
        }
    
        // Add functionality to menu options
        $('.bb-menu-option').on('click', function(event) {
            showPage($(this).attr('page'));
            
            return false;
        });
    });
    
    pSocket.on('update lobby', function(data) {
        if (data.property == 'state') {
            lobbyData.prevState = lobbyData.state;
        }
        
        lobbyData[data.property] = data.value;
        
        if (data.property in lobbyUIFunctions) {
            lobbyUIFunctions[data.property]();
        }
    });
    
    pSocket.on('lobby chat', function(data) {
        onLobbyChat($('#bb-lobby-chat-messages'), data, false);
    });
}

/**
 * Report a win to the server.
 * @param {string} participantId - The Challonge id of the winner.
 */
function reportWin(participantId) {
    pSocket.emit('report win', { 'player-id': participantId });
}


//////////////////////
// HELPER FUNCTIONS //
//////////////////////

/**
 * Get a content page's URL including tourney and participant data.
 * @param {string} pageName - The name of the page to load. Should exist at
 *   /app-content/<pageName>/<tourneyName>/<participantId>
 */
function getContentURL(pageName) {
    return '/app-content/' + pageName + '/' + tourneyName + '/' + participantId;
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
 * Create a "Report Win" button DOM element.
 * @param {string} participantId - The id of the participant we're reporting the win for.
 */
function createReportWinButton(participantId) {
    var btn = $('<a class="btn btn-app"><i class="fa fa-trophy"></i> Report Win</a>');
    
    btn.on('click', function(event) {
        reportWin(participantId);
    
        return false;
    });
    
    return btn;
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

//////////////////
// UI FUNCTIONS //
//////////////////

/**
 * Update the UI elements for every field in lobbyData.
 */
function updateLobbyUI() {
    for (prop in lobbyUIFunctions) {
        lobbyUIFunctions[prop]();
    }
}

/**
 * Update the timer text.
 */
function updateLobbyTimer() {
    var timeDiff = new Date(new Date() - new Date(lobbyData.startTime));
    var minStr = "" + timeDiff.getMinutes();
    var secStr = "" + timeDiff.getSeconds();

    $('#bb-timer').text(padString(minStr, 2, '0') + ":" + padString(secStr, 2, '0'));
}

/**
 * Show an app page, update the menu, and update the URL hash.
 * @param {string} pageName - The name of the page (see getContentURL()).
 */
function showPage(pageName) {
    if (!pSocket.connected) return;
    
    $('.bb-menu-option').removeClass('active');
    $('.bb-menu-option[page="' + pageName + '"]').addClass('active');
    
    $('.content-wrapper').load(getContentURL(pageName), pageSetup[pageName]);
        
    if (window.history.replaceState) {
        window.history.replaceState(null, null, '#' + pageName);
    }
    else {
        window.location.hash = pageName;
    }
    currentPage = pageName;
}

/**
 * Add a callout at the top of the app. If a callout with this id exists, replace it.
 * @param {string} id - Unique identifier for this callout (suffix to "bb-callout-").
 * @param {string} type - One of {danger, info, warning, success}.
 * @param {string} title - Callout title.
 * @param {string} message - Callout message.
 */
function addCallout(id, type, title, message) {
    removeCallout(id);
    
    
    var callout = $('<div class="callout callout-' + type + '" id="' + id + '"></div>');
    callout.append('<h4>' + title + '</h4>');
    callout.append('<p>' + message + '</p>');
    
    callout.insertBefore($('.widget-user'));
}

/**
 * Remove a callout from the top of the app.
 * @param {string} id - Unique identifier for this callout (suffix to "bb-callout-").
 */
function removeCallout(id) {
    $('#bb-callout-' + id).remove();
}

/**
 * Receive a lobby chat message.
 * @param {jQuery object} msgBox - The input element containing message text.
 * @param {json} msgData - Message JSON data.
 *     @param {string} msgData.name - The name of the sender.
 *     @param {string} msgData.sentTime - Date string representing the time the message was sent.
 *     @param {string} msgData.avatar - The sender's avatar.
 *     @param {string} msgData.message - The text of the message.
 *     @param {string} msgData.senderId - The Challonge participant id of the sender.
 * @param {string} msgData - The string.
 */
function onLobbyChat(msgBox, msgData, instant) {
    var msg = createChatMessage(msgData.name, msgData.sentTime, msgData.avatar,
                                msgData.message, msgData.senderId == participantId);
                                
    // Only scroll down if user is already at bottom
    var atBottom = msgBox.scrollTop() + msgBox.innerHeight() >= msgBox[0].scrollHeight;
    
    msg.appendTo(msgBox);
    
    // Do this after append so we can get the actual height
    if (atBottom && !instant) {
        msgBox.animate({ scrollTop: msgBox[0].scrollHeight }, "slow");
    }
}

/**
 * Send a message from a chat box and empty the chat box.
 * Does nothing if the box is empty.
 * @param {string} messageName - Name of the socketIO message to send with chat data.
 * @param {jQuery object} textBox - The input element containing message text.
 */
function sendChat(messageName, textBox) {
    var message = textBox.val();
    if (message == '') return;
    
    pSocket.emit(messageName, {
                 'message': message
    });
    
    textBox.val('');
}