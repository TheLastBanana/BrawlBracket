/* Text for a timer */
var Timer = React.createClass({
    getInitialState: function() {
        return {
            elapsed: this.props.startTime ? Math.floor((new Date() - new Date(this.props.startTime)) / 1000) : 0
        }
    },
    
    componentDidMount: function() {
        this.interval = setInterval(this._tick, 1000);
    },
    
    componentWillUnmount: function() {
        clearInterval(this.interval);
    },
    
    render: function() {
        var timeDiff = new Date();
        timeDiff.setTime(0);
        timeDiff.setSeconds(this.state.elapsed);
        
        return (
            <span>{getTimerString(timeDiff)}</span>
        );
    },
    
    _tick: function() {
        this.setState({
            elapsed: this.state.elapsed + 1
        });
    }
});

/* Displays a small piece of information */
var InfoWidget = React.createClass({
    render: function() {
        return (
            <div className="info-box bb-wait-for-match overlay-wrapper">
                <span className="info-box-icon bg-light-blue"><i className={'fa fa-' + this.props.icon}></i></span>
                <div className="info-box-content">
                    <span className="info-box-text">{this.props.title}</span>
                    <span className="info-box-number">{this.props.children}</span>
                </div>
            </div>
        );
    }
});

/* A row in the player info table */
var PlayerInfo = React.createClass({
    render: function() {
        var player = this.props.player;
        return (
            <tr>
                <td><div className="player-status" data-toggle="tooltip" data-original-title={player.status}></div></td>
                <td><img src={'/static/brawlbracket/img/legends-small/' + player.legend + '.png'}></img></td>
                <td>{player.name}</td>
            </tr>
        );
    }
});

/* The player info table */
var PlayerTable = React.createClass({
    render: function() {
        return (
            <div className="box box-solid bb-wait-for-match">
                <div className="box-header with-border">
                    <h4 className="box-title">Players</h4>
                </div>
                <div className="box-body no-padding">
                    <table className="table table-striped table-players">
                        <tbody>
                            {this.props.children}
                        </tbody>
                    </table>
                </div>
            </div>
        );
    }
});

/* Displays whether a team is ready */
var TeamReadyState = React.createClass({
    render: function() {
        var ready = this.props.ready;
        
        var color = ready ? 'green' : 'yellow';
        var status = ready ? 'Ready' : 'Not Ready';
        
        return (
            <h2 className={"description-status text-" + color}>
                {status}
            </h2>
        );
    }
});

/* Displays the matchup between the two teans, including readiness state and score reporting where appropriate */
var MatchupDisplay = React.createClass({
    render: function() {
        var teams = this.props.teams;
        
        return (
            <div className="box box-widget widget-user bb-wait-for-match">
                <div className="widget-user-header bg-green-active">
                    <h3 className="widget-user-username-versus-1">{teams[0].name} <sup>({teams[0].seed})</sup></h3>
                    <h3 className="widget-user-username-versus-center">vs</h3>
                    <h3 className="widget-user-username-versus-2">{teams[1].name} <sup>({teams[1].seed})</sup></h3>
                </div>
                <div className="widget-user-image-versus-1">
                    <img className="img-circle" src={teams[0].avatar} alt="User Avatar"></img>
                </div>
                <div className="widget-user-image-versus-2">
                    <img className="img-circle" src={teams[1].avatar} alt="User Avatar"></img>
                </div>
                <div className="box-footer">
                    <div className="row">
                        <div className="col-xs-5 border-right">
                            <div className="description-block">
                                <TeamReadyState ready={teams[0].ready} />
                            </div>
                        </div>
                    <div className="col-xs-2">
                        <div className="description-block" style={{margin: '0px', height: '85px'}}>
                            <h2 className="description-score">{teams[0].wins + '-' + teams[1].wins}</h2>
                            <span className="description-text">{'BEST OF ' + this.props.bestOf}</span>
                        </div>
                    </div>
                        <div className="col-xs-5 border-left">
                            <div className="description-block">
                                <TeamReadyState ready={teams[1].ready} />
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        );
    }
});

/* The whole lobby structure */
var Lobby = React.createClass({
    getInitialState: function() {
        return $.extend(true, {}, this.props.lobbyData);
    },
    
    render: function() {
        var infoWidgets = [];
        
        // Timer widget
        if (this.state.startTime) {
            infoWidgets.push(
                <div className="col-sm-12 col-lg-12" key="startTime">
                    <InfoWidget icon="clock-o" title="Time Since Start">
                        <Timer startTime={this.state.startTime} />
                    </InfoWidget>
                </div>
            );
        }
        
        // Room number widget
        if (this.state.roomNumber) {
            infoWidgets.push(
                <div className="col-sm-12 col-lg-12" key="roomNumber">
                    <InfoWidget icon="users" title="Room Number">
                        this.state.roomNumber
                    </InfoWidget>
                </div>
            );
        }
        
        // Current map widget
        if (this.state.currentRealm) {
            infoWidgets.push(
                <div className="col-sm-12 col-lg-12" key="currentRealm">
                    <InfoWidget icon="map" title="Current Map">
                        this.state.currentRealm
                    </InfoWidget>
                </div>
            );
        }
        
        // Create callout if necessary
        var calloutData;
        switch (this.state.state.name) {
            case 'building':
                calloutData = {
                    title: 'Your match is still being prepared!',
                    body: 'You shouldn\'t be seeing this message.',
                    color: 'danger'
                }
                break;
            
            case 'waitingForPlayers':
                calloutData = {
                    title: 'Your opponent hasn\'t joined the lobby yet!',
                    body: 'You\'ll be notified as soon as they\'re ready.',
                    color: 'warning'
                }
                break;
                
            case 'waitingForMatch':
                calloutData = {
                    title: 'Your opponent hasn\'t joined the lobby yet!',
                    body: 'You\'ll be notified as soon as match <strong>#' + this.state.state.matchNumber +
                          '</strong> (<strong>' + this.state.state.teamNames[0] +
                          '</strong> vs <strong>' + this.state.state.teamNames[1] + '</strong>) finishes.',
                    color: 'warning'
                }
                break;
        }
        
        var callout;
        if (calloutData) {
            callout = (
                <div className={'callout callout-' + calloutData.color}>
                    <h4>{calloutData.title}</h4>
                    <p>{calloutData.body}</p>
                </div>
            );
        }
        
        return (
            <div>
                {callout}
                
                <div className="row">
                    <div className="col-xs-12 col-lg-3 pull-left" id="sidebar-content">
                        <PlayerTable>
                            {this.state.players.map(function(player, i) {
                                return (
                                    <PlayerInfo player={player} key={i} />
                                );
                            })}
                        </PlayerTable>
                    </div>
                    
                    <div className="col-xs-12 col-lg-9 pull-right">
                        <div className="row">
                            <div className="col-lg-8">
                                <MatchupDisplay teams={this.state.teams} bestOf={this.state.bestOf} />
                            </div>
                  
                            <div className="col-lg-4">
                                <div className="row">
                                    {infoWidgets}
                                </div>
                            </div>
                        </div>
                  
                        <div id="bb-picker-content">
                        </div>
                    </div>
                
                    <div className="col-xs-12 col-lg-3 pull-left" id="sidebar-content">
                        <Chat
                            height="450px"
                            socket={this.props.chatSocket}
                            chatId={this.state.chatId}
                            chatCache={this.props.chatCache}
                        />
                    </div>
                </div>
            </div>
        );
    },
    
    componentDidMount: function() {
        this._updateLobbyNumber();
        
        this.props.mainSocket.on('update lobby', this._updateLobby);
    },
    
    componentWillUnmount: function() {
        this.props.mainSocket.off('update lobby', this._updateLobby);
    },
    
    _updateLobby: function(data) {
        var newData = $.extend(true, this.state.lobbyData, data);
        this.setState(newData);
        
        this._updateLobbyNumber();
    },
    
    // Kind of a hack, but oh well. Updates the lobby number in elements outside the lobby.
    _updateLobbyNumber: function() {
        var matchName = 'Match #' + this.state.number;
        $('.bb-page-name').text(matchName);
    }
});

function createLobby(container, lobbyData, mainSocket, chatSocket, chatCache) {
    ReactDOM.render(
        <Lobby
            lobbyData={lobbyData}
            mainSocket={mainSocket}
            chatSocket={chatSocket}
            chatCache={chatCache}
        />,
        container
    );
}