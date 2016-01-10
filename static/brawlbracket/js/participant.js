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
            $("#player1-report-win").on('click', function() {
                reportWin(lobbyData["player1-id"]);
            });
            
            $("#player2-report-win").on('click', function() {
                reportWin(lobbyData["player2-id"]);
            });
        });
    });
}

function reportWin(playerId) {
    pSocket.emit('report win', { 'player-id': playerId });
}