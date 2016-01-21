// Participant socket connection
var pSocket;
var lobbyData;
var currentPage;
var tourneyName;
var participantId;

// Functions to call after a page is loaded.
var pageSetup = {
    'lobby': function() {
        console.log(lobbyData);
    
        // Activate Report Win buttons
        $("#bb-par1-report-win").on('click', function() {
            reportWin(lobbyData.participants[0].id);
        });
        
        $("#bb-par2-report-win").on('click', function() {
            reportWin(lobbyData.participants[1].id);
        });
        
        // Lobby info
        $("#bb-room-number").text(lobbyData.roomNumber);
        $("#bb-current-realm").text(lobbyData.currentRealm);
        
        // Participant info
        $("#bb-par1-name").text(lobbyData.participants[0].name);
        $("#bb-par2-name").text(lobbyData.participants[1].name);
        $("#bb-par1-avatar").attr("src", lobbyData.participants[0].avatar);
        $("#bb-par2-avatar").attr("src", lobbyData.participants[1].avatar);
        
        // Player info
        $("#bb-pla1-name").text(lobbyData.players[0].name);
        $("#bb-pla2-name").text(lobbyData.players[1].name);
        
        legendBase = "/static/brawlbracket/img/legends-small/"
        $("#bb-pla1-legend").attr("src", legendBase + lobbyData.players[0].legend + ".png");
        $("#bb-pla2-legend").attr("src", legendBase + lobbyData.players[1].legend + ".png");
        
        $("#bb-pla1-status").attr("data-original-title", lobbyData.players[0].status);
        $("#bb-pla2-status").attr("data-original-title", lobbyData.players[1].status);
        
        currentPage = "lobby";
        
        // DEBUG
        //$("#bb-picker-content").load("/app-content/lobby-realms");
    }
};

$(window).on('beforeunload', function() {
    pSocket.close();
});

/*
    Connect to the server. Called when the app is first loaded.
*/
function brawlBracketInit(newTourneyName, newParticipantId) {
    tourneyName = newTourneyName;
    participantId = newParticipantId;
    
    pSocket = io.connect(window.location.origin + '/participant');

    pSocket.on('error', function() {
        $('.content').load(getContentURL('lobby-error'));
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
    });
    
    // Add functionality to menu options
    $('.bb-menu-option').on('click', function(event) {
        showPage($(this).attr('page'));
        event.preventDefault();
    });
}

/*
    Report a win to the server.
*/
function reportWin(playerId) {
    pSocket.emit('report win', { 'player-id': playerId });
}

/*
    Show the bracket page.
*/
function showPage(pageName) {
    $('.bb-menu-option').removeClass('active');
    $('.bb-menu-option[page="' + pageName + '"]').addClass('active');
    
    $('.content-wrapper').load(getContentURL(pageName), pageSetup[pageName]);
        
    window.location.hash = pageName;
    currentPage = pageName;
}

/*
    Get a content page's URL including tourney and participant data.
*/
function getContentURL(pageName) {
    return '/app-content/' + pageName + '/' + tourneyName + '/' + participantId;
}