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
                    onKeyDown={this._onKeyDown}
                    defaultValue={this.props.initialValue}
                    autoFocus={this.props.autoFocus}
                    onFocus={this.props.onFocus}
                    onBlur={this.props.onBlur}
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
    
    _onKeyDown: function(e) {
        // Escape key
        if (e.which == 27) {
            if (this.props.onEscape) {
                this.props.onEscape();
            }
        }
    },
    
    // Filter key presses
    _onKeyPress: function(e) {
        // Enter key
        if (e.which == 13) {
            this._callback();
        }
        
        // Validate numeric input
        if (this.props.number) {
            if (!(e.which > 47 && e.which < 58 || e.which == 8)) {
                e.preventDefault();
            }
        }
        
        // Validate length
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

// A text field which, when clicked, can be edited. The value will not actually be changed; the new value will be sent
// to this.props.callback to be handled appropriately
var EditableText = React.createClass({
    getInitialState: function() {
        return {
            editing: false
        };
    },
    
    render: function() {
        if (this.state.editing) {
            return (
                <TextEntry
                    extraClass={this.props.extraClass}
                    placeholder={this.props.placeholder}
                    number={this.props.number}
                    maxLength={this.props.maxLength}
                    autoFocus={true}
                    placeholder={this.props.text}
                    onBlur={this._cancelEditing}
                    onEscape={this._cancelEditing}
                    callback={this._saveEditing}
                />
            );
            
        } else {
            return (
                <div style={{lineHeight: '1em'}} onClick={this._startEditing}>
                    <span className="valign">{this.props.text}&nbsp;</span>
                    <i className="fa fa-pencil fa-sm text-light valign" />
                </div>
            );
        }
    },
    
    // Switch to edit mode
    _startEditing: function() {
        this.setState({
            editing: true
        });
    },
    
    // Exit edit mode and don't save changes
    _cancelEditing: function() {
        this.setState({
            editing: false
        });
    },
    
    // Save edited value
    _saveEditing: function(value) {
        this.setState({
            editing: false
        });
        
        if (this.props.callback) {
            this.props.callback(value);
        }
    }
});