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