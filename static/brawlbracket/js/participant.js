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
            $("#player1-report-win").on('click', function() {
                reportWin(lobbyData["player1-id"]);
            });
            
            $("#player2-report-win").on('click', function() {
                reportWin(lobbyData["player2-id"]);
            });
            
            // Set user info
            $(".widget-user-username-versus-1").text(lobbyData["player1-name"]);
            $(".widget-user-username-versus-2").text(lobbyData["player2-name"]);
            $("#participant-1-avatar").attr("src", lobbyData["player1-avatar"]);
            $("#participant-2-avatar").attr("src", lobbyData["player2-avatar"]);
        });
    });
}

function reportWin(playerId) {
    pSocket.emit('report win', { 'player-id': playerId });
}