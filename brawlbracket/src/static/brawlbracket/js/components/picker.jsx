'use strict';

/* Icon for a legend in the picker */
var LegendIcon = React.createClass({
    render: function() {
        return (
            <li>
                <a href="" className="bb-legend-option" onClick={this._onClick}>
                    <div className="legend-image-wrapper">
                        <img src={'/static/brawlbracket/img/legends/' + this.props.id + '.png'}></img>
                        <div className="legend-circle"></div>
                    </div>
                    <p>{this.props.name}</p>
                </a>
            </li>
        );
    },
    
    // Call back with the legend id
    _onClick: function(e) {
        if (this.props.callback) {
            this.props.callback(this.props.id);
        }
        
        e.preventDefault();
    }
});

/* Lets the user click a legend in the list and returns the data to a callback */
var LegendPicker = React.createClass({
    render: function() {
        var callback = this.props.callback;
        
        return (
            <ul className="legend-roster">
                {this.props.legendData.map(function(legend) {
                    return (
                        <LegendIcon
                            id={legend[0]}
                            name={legend[1]}
                            callback={callback}
                            key={legend[0]}
                        />
                    );
                })}
            </ul>
        );
    }
});

/* Icon for a realm in the picker */
var RealmIcon = React.createClass({
    render: function() {
        var className = 'realm-option';
        if (this.props.banned) {
            className += ' disabled';
        }
        
        // No callback, so just display maps
        if (this.props.callback === null || this.props.banned) {
            return (
                <li className={className}>
                    <img src={'/static/brawlbracket/img/realms/' + this.props.id + '.png'}></img>
                    <p>{this.props.name}</p>
                </li>
            );
            
        // Enabled picker
        } else {
            return (
                <li className={className}>
                    <a href="" onClick={this._onClick}>
                        <img src={'/static/brawlbracket/img/realms/' + this.props.id + '.png'}></img>
                        <p>{this.props.name}</p>
                    </a>
                </li>
            );
        }
    },
    
    // Call back with the legend id
    _onClick: function(e) {
        if (this.props.callback) {
            this.props.callback(this.props.id);
        }
        
        e.preventDefault();
    }
});

/* Lets the user click a realm in the list and returns the data to a callback */
var RealmPicker = React.createClass({
    render: function() {
        var callback = this.props.callback;
        var bans = this.props.bans;
        
        return (
            <ul className="realm-picker">
                {this.props.realmData.map(function(realm) {
                    return (
                        <RealmIcon
                            id={realm[0]}
                            name={realm[1]}
                            callback={callback}
                            banned={bans.indexOf(realm[0]) >= 0}
                            key={realm[0]}
                        />
                    );
                })}
            </ul>
        );
    }
});