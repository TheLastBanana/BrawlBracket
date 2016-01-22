// Participant socket connection
var pSocket;

// JSON data for lobby
var lobbyData;

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
        
        currentPage = "lobby";
        
        // DEBUG
        //$("#bb-picker-content").load("/app-content/lobby-realms");
    }
};

// Functions to update UI from lobbyData
var lobbyUIFunctions = {
    'participants': function () {
        participants = lobbyData.participants;
        
        // Add Report Win button functionality
        $("#bb-par1-report-win").on('click', function(event) {
            reportWin(lobbyData.participants[0].id);
            
            return false;
        });
        
        $("#bb-par2-report-win").on('click', function(event) {
            reportWin(lobbyData.participants[1].id);
            
            return false;
        });
        
        // Participant info
        $("#bb-par1-name").html(participants[0].name + " <sup>(" + participants[0].seed + ")</sup>");
        $("#bb-par2-name").html(participants[1].name + " <sup>(" + participants[1].seed + ")</sup>");
        $("#bb-par1-avatar").attr("src", participants[0].avatar);
        $("#bb-par2-avatar").attr("src", participants[1].avatar);
        
        // Show "report win" buttons when game is being played
        if (lobbyData.state.name == "inGame") {
            $("#bb-par1-description").html(getReportWinButtonHTML()).on('click', function(event) {
                reportWin(lobbyData.participants[0].id);
            
                return false;
            });
            
            $("#bb-par2-description").html(getReportWinButtonHTML()).on('click', function(event) {
                reportWin(lobbyData.participants[1].id);
            
                return false;
            });
        }
        // Update participant status
        else {
            $("#bb-par1-description").html(getStatusHTML(participants[0].ready));
            $("#bb-par2-description").html(getStatusHTML(participants[1].ready));
        }
    },
    
    'players': function () {
        players = lobbyData.players;
        
        // Player info
        $("#bb-pla1-name").text(lobbyData.players[0].name);
        $("#bb-pla2-name").text(lobbyData.players[1].name);
        
        legendBase = "/static/brawlbracket/img/legends-small/"
        $("#bb-pla1-legend").attr("src", legendBase + lobbyData.players[0].legend + ".png");
        $("#bb-pla2-legend").attr("src", legendBase + lobbyData.players[1].legend + ".png");
        
        $("#bb-pla1-status").attr("data-original-title", lobbyData.players[0].status);
        $("#bb-pla2-status").attr("data-original-title", lobbyData.players[1].status);
    },
    
    'state': function () {
        // Need to update buttons/participant status when entering/exiting inGame state
        if (lobbyData.state.name == 'inGame' || lobbyData.prevState.name == 'inGame') {
            lobbyUIFunctions.participants();
        }
    },
    
    'chatlog': function () {
        
    },
    
    'realmBans': function () {
        
    },
    
    'roomNumber': function () {
        $("#bb-room-number").text(lobbyData.roomNumber);
    },
    
    'currentRealm': function () {
        $("#bb-current-realm").text(lobbyData.currentRealm);
    },
    
    'challongeId': function () {
        matchName = "Match #" + lobbyData.challongeId;
        $(".bb-page-name").text(matchName);
    }
};

$(window).on('beforeunload', function() {
    pSocket.close();
});


//////////////////
// SOCKET STUFF //
//////////////////

/*
    Connect to the server. Called when the app is first loaded.
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
}

/*
    Report a win to the server.
*/
function reportWin(playerId) {
    pSocket.emit('report win', { 'player-id': playerId });
}


//////////////////////
// HELPER FUNCTIONS //
//////////////////////

/*
    Get a content page's URL including tourney and participant data.
*/
function getContentURL(pageName) {
    return '/app-content/' + pageName + '/' + tourneyName + '/' + participantId;
}

/*
    Get the HTML for participant status.
*/
function getStatusHTML(ready) {
    color = ready ? 'green' : 'yellow';
    status = ready ? 'Ready' : 'Not Ready';
    
    return '<h2 class="description-status text-' + color + '">' + status + '</h2>';
}

/*
    Get the HTML for a "Report Win" button.
*/
function getReportWinButtonHTML() {
    return '<a class="btn btn-app"><i class="fa fa-trophy"></i> Report Win</a>';
}

//////////////////
// UI FUNCTIONS //
//////////////////

/*
    Update the UI elements for every field in lobbyData.
*/
function updateLobbyUI() {
    for (prop in lobbyUIFunctions) {
        lobbyUIFunctions[prop]();
    }
}

/*
    Show the bracket page.
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