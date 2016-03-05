/**
 * Add a callout at the top of the app. If a callout with this id exists, replace it.
 * @param {string} id - Unique identifier for this callout (suffix to "bb-callout-").
 * @param {string} type - One of {danger, info, warning, success}.
 * @param {string} title - Callout title (optional).
 * @param {string} message - Callout message (optional).
 * @param {string} animation - 'in'/'inOut'/'none'. Optional.
 * @returns {jQuery object} The callout object.
 */
function addCallout(id, type, title, message, animation) {
    removeCallout(id);
    
    var callout = $('<div class="callout callout-' + type + '" id="' + id + '"></div>');
    if (title) callout.append('<h4>' + title + '</h4>');
    if (message) callout.append('<p>' + message + '</p>');
    
    $('.callout-container').prepend(callout);
    
    if (animation) {
        switch (animation) {
            case 'in':
                callout.hide().slideDown();
                break;
                
            case 'inOut':
                callout.hide().slideDown().delay(3000).slideUp();
                break;
                
            case 'none':
            default:
                break;
        }
    }
    
    return callout;
}

/**
 * Remove a callout from the top of the app.
 * @param {string} id - Unique identifier for this callout (suffix to "bb-callout-").
 */
function removeCallout(id) {
    $('#bb-callout-' + id).remove();
}