'use strict';

var BracketNode = React.createClass({
    render: function () {
        var teamData = this.props.teams;

        // Get names for each team
        var teamNames = [];
        for (var i = 0; i < 2; ++i) {
            teamNames.push(teamData[this.props.match.teams[i]]);
        }

        // If there are children, create a column for them
        var childColumn;
        var getTop = this.getTop;
        if (this.props.match.children) {
            childColumn = (
                <div className="bracket-column">
                    {this.props.match.children.map(function(childMatch) {
                        return (
                            <BracketNode match={childMatch} teams={teamData} hasParent={true} key={childMatch.id} ref={'child'+childMatch.id} />
                        );
                    })}
                </div>
            );
        }

        // Only add the connector if there's a parent node
        var connector;
        if (this.props.hasParent) {
            connector = <div className="bracket-connector" ref="connector"></div>;
        }

        var scores = this.props.match.scores;
        var winner = this.props.match.winner;

        return (
              <div className="bracket-row">
                {childColumn}
                <div className="bracket-column">
                    <div className="bracket-match" ref="match">
                        <div className="bracket-match-id">
                            <div className="bracket-match-id-circle">{this.props.match.id}</div>
                        </div>
                        <div className="bracket-match-inner">
                            {[0, 1].map(function(i) {
                                return (
                                    <div className={'bracket-team' + (winner == i ? '' : ' loser')} key={i}>
                                        <div className="bracket-team-name">{teamNames[i]}</div>
                                        <div className="bracket-team-score">{scores[i]}</div>
                                    </div>
                                );
                            })}
                        </div>
                        {connector}
                    </div>
                </div>
            </div>
        );
    },

    // Tell children to update connectors now that DOM has rendered
    componentDidMount: function() {
        var children = this.props.match.children;
        if (!children) return;

        for (var i = 0; i < children.length; ++i) {
            var refName = 'child' + children[i].id;

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
            var newTop = $(domNode).position().top + offset;

            domNode.css('top', newTop + 'px');
            domNode.css('height', -offset + 'px');
            domNode.addClass('up');
        }
    }
});

var Bracket = React.createClass({
    render: function () {
        var root = this.props.bracket.root;
        var teams = this.props.bracket.teams;

        return (
            <div className="bracket">
                <BracketNode match={root} teams={teams} />
            </div>
        );
    }
});

function createBracket(id, bracket) {
    ReactDOM.render(
        <Bracket bracket={bracket} />,
        document.getElementById(id)
    );
}
