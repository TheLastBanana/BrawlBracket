'use strict';

var Modal = ReactBootstrap.Modal;
var Button = ReactBootstrap.Button;

/* Icon to select a winning team */
var WinnerPickIcon = React.createClass({
    render: function() {
        return (
            <li className="winner-team-icon">
                <a href="" onClick={this._callback}>
                    <div>
                        <img src={this.props.avatar} />
                        <p>{this.props.name}</p>
                    </div>
                </a>
            </li>
        );
    },
    
    _callback: function(e) {
        this.props.callback(this.props.index);
        
        e.preventDefault();
    }
});

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
                <td><span className="label label-primary" data-toggle="tooltip" data-original-title="Seed">{this.props.seed}</span></td>
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
                            {this.props.teams.map(function(team, i) {
                                return (
                                    <PlayerInfo
                                        player={team.players[0]}
                                        seed={team.seed}
                                        key={i}
                                    />
                                );
                            })}
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
                    <h3 className="widget-user-username-versus-1">{teams[0].name}</h3>
                    <h3 className="widget-user-username-versus-center">vs</h3>
                    <h3 className="widget-user-username-versus-2">{teams[1].name}</h3>
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
        return $.extend(true, {
            modal: null,
            selectedWinner: null
        }, this.props.lobbyData);
    },
    
    render: function() {
        var infoWidgets = [];
        
        // Get info about player
        var myPlayerData = this._getPlayerDataByUserId(this.props.userId);
        var myTeam = myPlayerData[0];
        var myPlayer = myPlayerData[1];
        
        // Get the lowest seed team
        var sortedTeams = this.state.teams.slice();
        sortedTeams.sort(function(a, b) {
            return a.seed - b.seed;
        });
        var lowSeedTeam = sortedTeams[0];
        
        // This player is responsible for reporting scores, creating the room, etc.
        var leader = lowSeedTeam.players[0];
        
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
            var innerText;
            
            if (leader.id == myPlayer.id) {
                // Editable room number for leader
                innerText = (
                    <EditableText
                        text={this.state.roomNumber}
                        extraClass="input-lg"
                        placeholder="Room number"
                        number={true}
                        maxLength={5}
                        callback={this._setRoom}
                    />
                );
            } else {
                innerText = (
                    <span>{this.state.roomNumber}</span>
                );
            }
            
            infoWidgets.push(
                <div className="col-sm-12 col-lg-12" key="roomNumber">
                    <InfoWidget icon="users" title="Room Number">
                        {innerText}
                    </InfoWidget>
                </div>
            );
        }
        
        // Current map widget
        if (this.state.currentRealm) {
            var currentRealm = this.state.currentRealm;
            var currentRealmData = this.props.realmData.find(function (realm) {
                return realm[0] == currentRealm;
            });
            
            infoWidgets.push(
                <div className="col-sm-12 col-lg-12" key="currentRealm">
                    <InfoWidget icon="map" title="Current Map">
                        {currentRealmData ? currentRealmData[1] : 'Unsupported Realm'}
                    </InfoWidget>
                </div>
            );
        }
        
        // Create elements based on lobby state
        var calloutData;
        var stateBoxData;
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
                
            case 'pickLegends':
                // Not currently picking
                if (this.state.state.canPick.indexOf(this.props.userId) == -1) {
                    stateBoxData = {
                        title: 'Please wait',
                        icon: 'hourglass-half',
                        contents: (
                            <div>Your opponent is currently picking their legend!</div>
                        )
                    }
                    
                // Currently picking
                } else {
                    stateBoxData = {
                        title: 'Pick your legend',
                        icon: 'user',
                        contents: (
                            <LegendPicker
                                legendData={this.props.legendData}
                                callback={this._pickLegend}
                            />
                        )
                    }
                }
                break;
                
            case 'chooseMap':
                var choosePlayer = this._getPlayerDataByUserId(this.state.state.turn)[1];
                
                // If multiple bans are remaining, show plural form and remaining count
                var countText = 'a realm';
                if (this.state.state.remaining) {
                    countText = 'realms (' + this.state.state.remaining  + ' remaining)';
                }
                
                if (this.state.state.turn == this.props.userId) {
                    switch (this.state.state.action) {
                        case 'ban':
                            stateBoxData = {
                                title: 'Ban ' + countText,
                                icon: 'ban',
                                contents: (
                                    <RealmPicker
                                        realmData={this.props.realmData}
                                        bans={this.state.realmBans}
                                        callback={this._banRealm}
                                        action="ban"
                                    />
                                )
                            }
                            break;
                            
                        case 'pick':
                            stateBoxData = {
                                title: 'Pick ' + countText,
                                icon: 'check-circle-o',
                                contents: (
                                    <RealmPicker
                                        realmData={this.props.realmData}
                                        bans={this.state.realmBans}
                                        callback={this._pickRealm}
                                        action="pick"
                                    />
                                )
                            }
                            break;
                    }
                    break;
                } else {
                    // Another user is picking maps
                    stateBoxData = {
                        title: choosePlayer.name + '\'s turn to ' + this.state.state.action + ' ' + countText,
                        icon: 'hourglass-half',
                        contents: (
                            <RealmPicker
                                realmData={this.props.realmData}
                                bans={this.state.realmBans}
                            />
                        )
                    }
                }
                break;
                
            case 'createRoom':
                if (leader.id == myPlayer.id) {
                    // Tell the user to create a room
                    stateBoxData = {
                        title: 'Time to create a room in-game',
                        icon: 'plus-circle',
                        contents:
                            <div>
                                <p>Create a <strong>private</strong> game in Brawlhalla by going to Custom Online > Private Game in the main menu.</p>
                                <p>Make sure you've changed the following game settings:</p>
                                <ul>
                                    <li>Game mode: <strong>Stock</strong></li>
                                </ul>
                                <p>When you're done, enter the room number here:</p>
                                <TextEntry
                                    extraClass="input-lg"
                                    placeholder="Room number"
                                    number={true}
                                    maxLength={5}
                                    callback={this._setRoom}
                                />
                            </div>
                    }
                    
                } else {
                    // Another user is creating the room
                    stateBoxData = {
                        title: 'Please wait',
                        icon: 'hourglass-half',
                        contents: (
                            <div>
                                {leader.name} is creating a room for you to join in-game. You'll be notified when it's ready.
                            </div>
                        )
                    }
                }
                break;
                
            case 'inGame':
                if (leader.id == myPlayer.id) {
                    var selectWinner = this._selectWinner;
                    
                    stateBoxData = {
                        title: 'Score reporting',
                        icon: 'trophy',
                        contents: (
                            <div>
                                <p>When you've finished playing the current game, report the score by clicking the winner below:</p>
                                <ul className="winner-team-picker">
                                    {this.state.teams.map(function (team, index) {
                                        return (
                                            <WinnerPickIcon
                                                key={index}
                                                index={index}
                                                avatar={team.avatar}
                                                name={team.name}
                                                callback={selectWinner}
                                            />
                                        );
                                    })}
                                </ul>
                            </div>
                        )
                    }
                } else {
                    stateBoxData = {
                        title: 'Ready to play!',
                        icon: 'gamepad',
                        contents: (
                            <div>
                                Go to Custom Online > Private Game in Brawlhalla and join <strong>room #{this.state.roomNumber}</strong>!
                            </div>
                        )
                    }
                }
                break;
        }
        
        // Callout at top of page
        var callout;
        if (calloutData) {
            callout = (
                <div className={'callout callout-' + calloutData.color}>
                    <h4>{calloutData.title}</h4>
                    {calloutData.body}
                </div>
            );
        }
        
        // Box holding interactive lobby state (legend picker, etc.)
        var stateBox;
        if (stateBoxData) {
            stateBox = (
                <div className="box box-primary">
                    <div className="box-header with-border">
                        <h3 className="box-title">
                            <i className={'fa fa-' + stateBoxData.icon}></i> {stateBoxData.title}
                        </h3>
                    </div>
                    
                    <div className="box-body">
                        {stateBoxData.contents}
                    </div>
                </div>
            );
        }
        
        // Modal to display
        var modal;
        switch (this.state.modal) {
            case 'confirmWinner':
                var teamName = this.state.teams[this.state.selectedWinner].name;
            
                modal = (
                    <Modal show={true} onHide={this.close}>
                        <Modal.Header>
                            <Modal.Title>Confirm your selection</Modal.Title>
                        </Modal.Header>

                        <Modal.Body>
                            Are you sure you want to set {teamName} as the winner for this game?
                        </Modal.Body>

                        <Modal.Footer>
                            <div className="pull-left"><Button onClick={this._closeModal}>Cancel</Button></div>
                            <Button bsStyle="primary" onClick={this._reportWin}>Yes</Button>
                        </Modal.Footer>
                    </Modal>
                );
                break;
        }
        
        return (
            <div>
                {modal}
            
                {callout}
                
                <div className="row">
                    <div className="col-lg-6 col-lg-push-3 col-md-6 col-md-push-6">
                        <MatchupDisplay teams={this.state.teams} bestOf={this.state.bestOf} />
                        
                        {stateBox}
                    </div>
                    
                    <div className="col-lg-3 col-lg-pull-6 col-md-6 col-md-pull-6">
                        <PlayerTable
                            teams={this.state.teams}
                        />
                        
                        <Chat
                            height="450px"
                            socket={this.props.chatSocket}
                            chatId={this.state.chatId}
                            chatCache={this.props.chatCache}
                            userId={this.props.userId}
                        />
                    </div>
          
                    <div className="col-lg-3">
                        <div className="row">
                            {infoWidgets}
                        </div>
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
        var newData = $.extend(true, this.state, data);
        this.setState(newData);
        
        this._updateLobbyNumber();
    },
    
    // Kind of a hack, but oh well. Updates the lobby number in elements outside the lobby.
    _updateLobbyNumber: function() {
        var matchName = 'Match #' + this.state.number;
        $('.bb-page-name').text(matchName);
    },
    
    // Get the player and team corresponding to a user id
    _getPlayerDataByUserId: function(userId) {
        var teams = this.state.teams;
        
        for (var i = 0; i < teams.length; ++i) {
            var players = teams[i].players;
            
            for (var j = 0; j < players.length; ++j) {
                if (players[j].id == userId) {
                    return [teams[i], players[j]];
                }
            }
        }
        
        return null;
    },
    
    // Tell the server a legend has been picked
    _pickLegend: function(legendId) {
        this.props.mainSocket.emit('pick legend', {
            legendId: legendId
        });
    },
    
    // Tell the server a realm has been banned
    _banRealm: function(realmId) {
        this.props.mainSocket.emit('ban realm', {
            realmId: realmId
        });
    },
    
    // Tell the server a realm has been picked
    _pickRealm: function(realmId) {
        this.props.mainSocket.emit('pick realm', {
            realmId: realmId
        });
    },
    
    // Tell the server that the room number has been set
    _setRoom: function(roomNumber) {
        this.props.mainSocket.emit('set room', {
            roomNumber: roomNumber
        });
    },
    
    // Select the winning team. This will show a confirmation modal
    _selectWinner: function(teamIndex) {
        var newData = $.extend(true, this.state, {
            modal: 'confirmWinner',
            selectedWinner: teamIndex
        });
        this.setState(newData);
    },
    
    // Report a win for a team.
    // Note that we report the team's index in lobbyData.teams, so we assume that the order of teams is the same on the
    // server and the client.
    _reportWin: function() {
        this.props.mainSocket.emit('report win', {
            teamIndex: this.state.selectedWinner
        });
        
        this._closeModal();
    },
    
    // Close the visible modal
    _closeModal: function() {
        var newData = $.extend(true, this.state, {
            modal: null
        });
        this.setState(newData);
    }
});