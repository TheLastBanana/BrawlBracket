'use strict';

var BracketTeam = React.createClass({
    render: function() {
        return (
            <div
                className=
                {
                    'bracket-team'
                    + (this.props.loser ? ' loser' : '')
                    + (this.props.highlight ? ' highlight' : '')
                }
                onMouseOver={this.onMouseOver}
                onMouseLeave={this.onMouseLeave}
            >
                <div className="bracket-team-seed">{this.props.seed}</div>
                <div className="bracket-team-name" title={this.props.name}>{this.props.name}</div>
                <div className="bracket-team-score">{this.props.score}</div>
            </div>
        );
    },

    onMouseOver: function() {
        if (this.props.id === null) return;

        this.props.setHighlightTeam(this.props.id);
    },

    onMouseLeave: function() {
        if (this.props.id === null) return;
        
        this.props.setHighlightTeam(-1, this.props.id);
    }
});

var BracketNode = React.createClass({
    render: function () {
        var teamData = this.props.teams;
        var matchData = this.props.matches;
        var highlightTeam = this.props.highlightTeam;
        var setHighlightTeam = this.props.setHighlightTeam;

        var match = matchData[this.props.root];
        var matchTeams = match.teams;
        var score = match.score;
        var winner = match.winner;
        var isHighlight = matchTeams.indexOf(highlightTeam) != -1;

        // Get data for each team
        var teamProps = [];
        for (var i = 0; i < 2; ++i) {
            var team = teamData[matchTeams[i]];
            if (team) {
                teamProps.push({
                    name: team.name,
                    seed: team.seed
                });
                
            } else {
                teamProps.push({
                    name: '',
                    seed: ''
                })
            }
        }

        // If there are children, create a column for them
        var childColumn;
        var getTop = this.getTop;
        if (match.prereqMatches) {
            childColumn = (
                <div className="bracket-column">
                    {match.prereqMatches.map(function(childMatch) {
                        return childMatch ? (
                            <BracketNode
                                root={childMatch}
                                teams={teamData}
                                matches={matchData}
                                hasParent={true}
                                highlightTeam={highlightTeam}
                                setHighlightTeam={setHighlightTeam}
                                key={childMatch}
                                ref={'child'+childMatch} />
                        ) : '';
                    })}
                </div>
            );
        }

        // Only add the connector if there's a parent node
        var connector;
        if (this.props.hasParent) {
            // If the highlight team lost, the connector is irrelevant
            var highlightConnector = isHighlight && (highlightTeam == matchTeams[winner]);
            connector = (
                <div
                    ref="connector"
                    className={'bracket-connector' + (highlightConnector ? ' highlight' : '')} >
                </div>
            );
        }

        // Create team DOM nodes
        var teamNodes = [];
        for (var i = 0; i < 2; ++i) {
            teamNodes.push(
                <BracketTeam
                    id={matchTeams[i]}
                    loser={!(winner === null) && winner != i}
                    highlight={matchTeams[i] == highlightTeam}
                    name={teamProps[i].name}
                    seed={teamProps[i].seed}
                    score={score[i]}
                    setHighlightTeam={setHighlightTeam}
                    key={i} />
            );
        }

        return (
              <div className="bracket-row">
                {childColumn}
                <div className="bracket-column">
                    <div className={'bracket-match' + (isHighlight ? ' highlight' : '')} ref="match">
                        <div className="bracket-match-id">
                            <div className="bracket-match-id-circle">{match.id}</div>
                        </div>
                        <div className="bracket-match-inner">
                            {teamNodes}
                        </div>
                        {connector}
                    </div>
                </div>
            </div>
        );
    },

    // Tell children to update connectors now that DOM has rendered
    componentDidMount: function() {
        var prereqMatches = this.props.matches[this.props.root].prereqMatches;
        if (!prereqMatches) return;

        for (var i = 0; i < prereqMatches.length; ++i) {
            var refName = 'child' + prereqMatches[i];

            if (this.refs[refName]) {
                this.refs[refName].updateConnector(this.getTop());
            }
        }
    },

    // Get the top of the match node
    getTop: function () {
        var domNode = this.refs.match;
        return $(domNode).position().top;
    },

    // Update connector height
    updateConnector: function(parentTop) {
        var domNode = $(this.refs.connector);
        var offset = parentTop - this.getTop();

        // Connector goes down
        if (offset > 0) {
            domNode.css('height', offset + 'px');

        // Connector goes up, so we need to offset it
        } else if (offset < 0) {
            // Use right border width, because top/bottom borders may not be set depending
            // on whether the 'up' class is already being used
            var lineWidth = parseInt(domNode.css('border-right-width'));
            var newTop = domNode.position().top + offset + lineWidth;

            domNode.css('top', newTop + 'px');
            domNode.css('height', -offset + 'px');
        }
    }
});

var BracketRounds = React.createClass({
    render: function () {
        var rounds = [];
        for (var i = 0; i < this.props.numRounds; ++i) {
            var name;
            if (i == this.props.numRounds - 1) {
                name = 'Finals';

            } else if (i == this.props.numRounds - 2 && this.props.numRounds >= 2) {
                name = 'Semifinals';

            } else {
                name = 'Round ' + (i + 1);
            }

            rounds.push(
                <div className="bracket-round" key={i}>
                    <div className="bracket-round-inner">{name}</div>
                </div>
            );
        }

        return (
            <div className="bracket-rounds-container" ref="rounds">{rounds}</div>
        );
    },

    componentDidMount: function () {
        this.pinRounds();
    },

    componentDidUpdate: function () {
        this.pinRounds();
    },

    // Pin to the bracket's outer div
    pinRounds: function () {
        $(this.refs.rounds).pin({
            containerSelector: '.bracket'
        });
    }
});

var Bracket = React.createClass({
    getInitialState: function() {
        return {
            teams: this.props.bracket.teams,
            matches: this.props.bracket.matches,
            root: this.props.bracket.root,
            highlightTeam: -1
        }
    },

    render: function () {
        var matches = this.state.matches;

        // Get the depth of the tree starting from a match
        var getDepth = function(matchId) {
            var match = matches[matchId];

            if (!match) return 0;
            if (!match.prereqMatches) return 1;

            return Math.max.apply(Math, match.prereqMatches.map(getDepth)) + 1;
        }

        // Rounds = depth of tree from root match
        var numRounds = getDepth(this.state.root);

        return (
            <div className="bracket">
                <BracketRounds numRounds={numRounds} />
                <div className="bracket-inner">
                    <BracketNode
                        root={this.state.root}
                        teams={this.state.teams}
                        matches={this.state.matches}
                        highlightTeam={this.state.highlightTeam}
                        setHighlightTeam={this.setHighlightTeam} />
                </div>
            </div>
        );
    },

    // Set the highlighted team.
    // If old is specified, the team will only be changed if the current highlightTeam == old.
    setHighlightTeam: function(team, old) {
        if (old && this.state.highlightTeam != old) return;

        this.setState({
            highlightTeam: team
        });
    }
});

/*
    id is the id of the DOM element to fill with the bracket.
    bracket should be of this format:
    {
        teams: {
            <uuid>: {
                name: <name>,
                seed: <seed>
            },
            ...
        },

        matches: {
            <uuid>: {
                id: <display id>,
                teams: [<team uuid>, ...],
                score: [<team score>, ...],
                winner: <index into teams>,
                prereqMatches: [<match uuid>, ...]
            },
            ...
        },

        root: <match uuid>
    }
*/
function createBracket(id, bracket) {
    ReactDOM.render(
        <Bracket bracket={bracket} />,
        document.getElementById(id)
    );
}
