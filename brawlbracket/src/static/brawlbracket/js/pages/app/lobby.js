function initLobby(legendData, realmData) {
    ReactDOM.render(
        React.createElement(Lobby,
            {
                lobbyData: lobbyData,
                mainSocket: tSocket,
                chatSocket: chatSocket,
                chatCache: chatCache,
                legendData: legendData,
                realmData: realmData,
                userId: userId
            }
        ),
        $('#lobby').get(0)
    );
}