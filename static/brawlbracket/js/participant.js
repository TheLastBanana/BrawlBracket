// Participant socket connection
var pSocket;

function participantConnect() {
    pSocket = io.connect(window.location.origin + '/participant');

    pSocket.on('error', function() {
        $(".content").load("/app-content/lobby-error");
    });
    
    pSocket.on('connect', function() {
        console.log('connected');
    });
    
    pSocket.on('join lobby', function(lobbyData) {
        console.log(lobbyData)
        $(".content").load("/app-content/lobby", function() {
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
            
            // DEBUG
            $("#bb-picker-content").load("/app-content/lobby-realms");
        });
    });
}

function reportWin(playerId) {
    pSocket.emit('report win', { 'player-id': playerId });
}

$(window).on('beforeunload', function() {
    pSocket.close();
});