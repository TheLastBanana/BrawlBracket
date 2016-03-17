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

/* Lets the user click a single legend in the list and returns the data to a callback */
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