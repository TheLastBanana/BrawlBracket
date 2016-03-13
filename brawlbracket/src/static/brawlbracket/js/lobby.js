// Lobby timer interval so it can be cleared/checked later
var lobbyTimer;

// Functions to update UI from lobbyData
var lobbyUIFunctions = {
    'teams': function () {
        var teams = lobbyData.teams;
        
        if (lobbyData.state.name == 'waitingForMatch') return;
        if (teams.length != 2) return;
        
        // Add Report Win button functionality
        $('#bb-par1-report-win').on('click', function(event) {
            reportWin(teams[0].id);
            
            return false;
        });
        
        $('#bb-par2-report-win').on('click', function(event) {
            reportWin(teams[1].id);
            
            return false;
        });
        
        // Team info
        $('#bb-par1-name').text(teams[0].name + ' ').append('<sup>(' + teams[0].seed + ')</sup>');
        $('#bb-par2-name').text(teams[1].name + ' ').append('<sup>(' + teams[1].seed + ')</sup>');
        $('#bb-par1-avatar').attr('src', teams[0].avatar);
        $('#bb-par2-avatar').attr('src', teams[1].avatar);
        $('#bb-score').text(teams[0].wins + '-' + teams[1].wins);
        
        // Show "report win" buttons when game is being played
        if (lobbyData.state.name == 'inGame') {
            $('#bb-par1-description').html(createReportWinButton(teams[0].id));
            $('#bb-par2-description').html(createReportWinButton(teams[1].id));
        }
        // Update team status
        else {
            $('#bb-par1-description').html(createStatus(teams[0].ready));
            $('#bb-par2-description').html(createStatus(teams[1].ready));
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
            case 'building':
                // Disable everything and put spinners on them.
                $('.bb-wait-for-match').append(
                    $('<div class="overlay"><i class="fa fa-circle-o-notch fa-spin"></i></div>')
                );
                
                addCallout('state', 'warning',
                           'Your match is still being prepared!');
                           
                break;
            
            case 'waitingForMatch':
                // Disable everything and put spinners on them.
                $('.bb-wait-for-match').append(
                    $('<div class="overlay"><i class="fa fa-circle-o-notch fa-spin"></i></div>')
                );
                
                // Add a notice at the top about the prerequisite match.
                var msg = 'You\'ll be notified as soon as match <strong>#' + lobbyData.state.matchNumber +
                          '</strong> (<strong>' + lobbyData.state.teamNames[0] +
                          '</strong> vs <strong>' + lobbyData.state.teamNames[1] + '</strong>) finishes.';
                
                addCallout('state', 'warning',
                           'Your opponent hasn\'t finished their game yet!',
                           msg);
                           
                break;
                
            case 'waitingForPlayers':
                // Add a notice about the player missing.
                addCallout('state', 'warning',
                           'Your opponent hasn\'t joined the lobby yet!',
                           'You\'ll be notified as soon as they\'re ready.');
                break;
                
            case 'inGame':
                // Replace status with "report win" buttons
                lobbyUIFunctions.teams();
                break;
        }
        
        switch (lobbyData.prevState.name) {
            case 'inGame':
                // Replace "report win" buttons with status
                lobbyUIFunctions.teams();
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
        if (!lobbyTimer) lobbyTimer = setInterval(updateLobbyTimer, 1000);
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
        var matchName = 'Match #' + lobbyData.number;
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
    for (property in data) {
        if (property in lobbyUIFunctions) {
            lobbyUIFunctions[property]();
        }
    }
}

/**
 * Report a win to the server.
 * @param {string} teamId - The Challonge id of the winner.
 */
function reportWin(teamId) {
    pSocket.emit('report win', { 'player-id': teamId });
}

/**
 * Create a "Report Win" button DOM element.
 * @param {string} teamId - The id of the team we're reporting the win for.
 */
function createReportWinButton(teamId) {
    var btn = $('<a class="btn btn-app"><i class="fa fa-trophy"></i> Report Win</a>');
    
    btn.on('click', function(event) {
        reportWin(teamId);
    
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
    $('#bb-timer').text(getTimerString(lobbyData.startTime));
}

/**
 * Create a team status DOM element.
 * @param {boolean} ready - If true, the status is "Ready," else "Not Ready."
 */
function createStatus(ready) {
    var color = ready ? 'green' : 'yellow';
    var status = ready ? 'Ready' : 'Not Ready';
    
    return $('<h2 class="description-status text-' + color + '">' + status + '</h2>');
}

$(function() {
    pSocket.on('update lobby', onUpdateLobby);
    updateLobbyUI();

    // Called when the inner page content is removed to load a new page.
    // Clean up socketIO handlers.
    $('.content').on('destroy', function() {
        chatSocket.off('update lobby', onUpdateLobby);
        clearInterval(lobbyTimer);
        lobbyTimer = null;
    });
});