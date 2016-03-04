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

// JSON data for user settings
var userSettings;

function onSuccess() {
    addCallout('settings', 'success', '', 'Settings updated!', 'inOut');
}

function onFail() {
    addCallout('settings', 'danger', '', 'Failed to update settings. Please try again!', 'inOut');
}

/**
 * Set the settings form to current values.
 */
function resetUserSettingsForm() {
    // Check the appropriate radio button
    $('input[name="preferred-server"]').each(function() {
        $(this).prop('checked', $(this).attr('value') == userSettings.preferredServer);  
    });
    
    // Select owned legends
    $('.bb-legend-option').each(function() {
        if ($.inArray($(this).attr('legend'), userSettings.ownedLegends) == -1) {
            $(this).addClass('disabled');
        }
        else {
            $(this).removeClass('disabled');
        }
    });
}

/**
 * Save the user settings and send them to the server.
 */
function saveUserSettings() {
    // Find the checked preferred-server input
    userSettings.preferredServer = $('input[name="preferred-server"]:checked').val();
    
    userSettings.ownedLegends = []
    $('.bb-legend-option').each(function() {
        // If not disabled, then this legend is selected
        if (!$(this).hasClass('disabled')) {
            userSettings.ownedLegends.push($(this).attr('legend'));
        }
    });
    
    $.ajax({
        url: '/settings/',
        type: 'PUT',
        contentType: 'application/json',
        dataType: 'json',
        success: onSuccess,
        error: onFail,
        data: JSON.stringify(userSettings)
    });
}

/**
 * Initialize user settings page.
 * @param {json} initialSettings - The user settings provided by the server.
 */
function initUserSettingsPage(initialSettings) {
    userSettings = initialSettings;
    
    // Set legend picker title
    $('.bb-legend-picker .box-title').html('<i class="fa fa-users"></i> Click any legends you don\'t own');

    // Everyone "owns" random, so don't show it
    $('.bb-legend-option[legend="random"]').parent().remove();


    // Activate legend button controls
    $('.bb-legend-option').click(function() {
        $(this).toggleDisabled();
        
        return false;
    });

    $('#bb-roster-invert-sel').click(function() {
        $('.bb-legend-option').toggleDisabled();
        
        return false;
    });

    $('#bb-roster-select-all').click(function() {
       $('.bb-legend-option').removeClass('disabled');
        
        return false;
    });

    $('#bb-roster-deselect-all').click(function() {
       $('.bb-legend-option').addClass('disabled');
        
        return false;
    });

    // Save button sends new settings to server
    $('#bb-save-settings').click(function() {
        saveUserSettings();
        
        return false;
    });

    // Cancel button just resets
    $('#bb-reset-settings').click(function() {
        resetUserSettingsForm();
        
        return false;
    });

    // Select current settings
    resetUserSettingsForm();
    
    /*
    pSocket.on('update settings', onUpdateSettings);
    pSocket.on('invalid settings', onInvalidSettings);


    // Called when the inner page content is removed to load a new page.
    // Clean up socketIO handlers.
    $('.content').on('destroy', function() {
        pSocket.off('update settings', onUpdateSettings);
        pSocket.off('invalid settings', onInvalidSettings);
    });
    */
}

$.fn.extend({
    toggleDisabled: function() {
        return $(this).each(function() {
            if ($(this).hasClass('disabled')) {
                $(this).removeClass('disabled');
            }
            else {
                $(this).addClass('disabled');
            }
        });
    }
});