'use strict';

/**
 * Icon for a legend in the picker.
 *
 * @prop {string}   id          - Legend's short id name
 * @prop {string}   name        - Legend's full name
 * @prop {function} callback    - Callback function when clicked
 */
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

/**
 * Lists legends for the player to select.
 *
 * @prop {array}    legendData  - Data for selectable legends. Pairs of (short name, full name)
 * @prop {function} callback    - Callback when a legend is clicked
 */
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

/**
 * Icon for a realm in the picker.
 *
 * @prop {string}   id          - Realm's short id name
 * @prop {string}   name        - Realm's full name
 * @prop {function} callback    - Callback function when clicked
 * @prop {boolean}  banned      - Whether this realm has been banned
 * @prop {string}   action      - What the player is doing. One of ['pick', 'ban']
 */
var RealmIcon = React.createClass({
    render: function() {
        var className = 'realm-option';
        if (this.props.banned) {
            className += ' disabled';
        }
        
        var actionIcon;
        switch (this.props.action) {
            case 'pick':
                actionIcon = 'check';
                break;
                
            case 'ban':
                actionIcon = 'times';
        }
        
        var inner = (
            <div>
                <div className="realm-icon">
                    <div className="action-symbol"><i className={'fa fa-' + actionIcon} /></div>
                    <img src={'/static/brawlbracket/img/realms/' + this.props.id + '.png'}></img>
                </div>
                <p>{this.props.name}</p>
            </div>
        );
        
        // No callback, so just display maps
        if (this.props.callback === null || this.props.banned) {
            return (
                <li className={className}>
                    {inner}
                </li>
            );
            
        // Enabled picker
        } else {
            return (
                <li className={className}>
                    <a href="" onClick={this._onClick}>
                        {inner}
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

/**
 * Lists legends for the player to pick/ban.
 *
 * @prop {array}    realmData   - Data for selectable realms. Pairs of (short name, full name)
 * @prop {array}    bans        - Short names of banned realms
 * @prop {string}   action      - What the player is doing. One of ['pick', 'ban']
 * @prop {function} callback    - Callback when a legend is clicked
 */
var RealmPicker = React.createClass({
    render: function() {
        var callback = this.props.callback;
        var bans = this.props.bans;
        var action = this.props.action;
        
        return (
            <ul className={'realm-picker ' + action}>
                {this.props.realmData.map(function(realm) {
                    return (
                        <RealmIcon
                            id={realm[0]}
                            name={realm[1]}
                            callback={callback ? callback : null}
                            banned={bans.indexOf(realm[0]) >= 0}
                            action={action}
                            key={realm[0]}
                        />
                    );
                })}
            </ul>
        );
    }
});