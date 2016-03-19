'use strict';

/* A simple text input with a submit button. Also responds to enter key. */
var TextEntry = React.createClass({
    render: function() {
        // Contents of button. Defaults to right arrow icon
        var btnContents = this.props.btnContents || (
            <i className="fa fa-arrow-right" />
        );
        
        // Extra class added to both inputs (useful for different sizes)
        var extraClass = '';
        if (this.props.extraClass) {
            extraClass = ' ' + this.props.extraClass;
        }
        
        return (
            <div className="input-group">
                <input
                    className={'form-control' + extraClass}
                    placeholder={this.props.placeholder}
                    onKeyPress={this._onKeyPress}
                    ref="textField"
                />
                <span className="input-group-btn">
                    <button className={'btn btn-info btn-flat' + extraClass} type="button" onClick={this._callback}>
                        {btnContents}
                    </button>
                </span>
            </div>
        );
    },
    
    // Filter key presses
    _onKeyPress: function(e) {
        if (e.which == 13) {
            this._callback();
        }
        
        if (this.props.number) {
            if (!(e.which > 47 && e.which < 58 || e.which == 8)) {
                e.preventDefault();
            }
        }
        
        if (this.props.maxLength && this.refs.textField.value.length >= this.props.maxLength) {
            e.preventDefault();
        }
    },
    
    _callback: function () {
        if (this.props.callback) {
            var value = this.refs.textField.value;
            if (this.props.number) {
                value = parseInt(value);
            }
            
            this.props.callback(value);
        }
    }
});