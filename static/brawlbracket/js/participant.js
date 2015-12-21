// Participant socket connection
var pSocket;

function participantConnect() {
    pSocket = io.connect(window.location.origin + '/participant');

    pSocket.on('error', function() {
        console.log('rejected');
    });
    
    pSocket.on('connect', function() {
        console.log('connected');
    });
}