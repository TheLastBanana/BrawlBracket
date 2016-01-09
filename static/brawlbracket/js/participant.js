// Participant socket connection
var pSocket;

function participantConnect() {
    pSocket = io.connect(window.location.origin + '/participant');

    pSocket.on('error', function() {
        $(".content").load("/app-content/lobby-error");
    });
    
    pSocket.on('connect', function() {
        $(".content").load("/app-content/lobby");
    });
}