// Lobby timer interval so it can be cleared/checked later
var lobbyTimer;

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
                
            case 'waitingForPlayers':
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
    
    'chatId': function () {
        $('.direct-chat').setUpChatBox(lobbyData.chatId);
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

/**
 * Update UI when lobby is updated.
 * @param {json} data - Data received from the socket.
 *      @param {string} data.property - The property of lobbyData to update.
 *      @param {json} data.value - The new value.    
 */
function onUpdateLobby(data) {
    if (data.property in lobbyUIFunctions) {
        lobbyUIFunctions[data.property]();
    }
}

/**
 * Report a win to the server.
 * @param {string} participantId - The Challonge id of the winner.
 */
function reportWin(participantId) {
    pSocket.emit('report win', { 'player-id': participantId });
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

// Code below is called when lobby is loaded
pSocket.on('update lobby', onUpdateLobby);
updateLobbyUI();

// Called when the inner page content is removed to load a new page.
// Clean up socketIO handlers.
$('.content').on('destroy', function() {
    chatSocket.off('update lobby', onUpdateLobby);
});