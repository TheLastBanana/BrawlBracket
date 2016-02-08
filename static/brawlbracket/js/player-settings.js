function onUpdateSettings(newSettings) {
    playerSettings = newSettings;
        
    if (currentPage == 'player-settings') {
        addCallout('settings', 'success', '', 'Settings updated!', 'inOut');
    }
}

function onInvalidSettings() {
    if (currentPage == 'player-settings') {
        addCallout('settings', 'danger', '', 'Failed to update settings. Please try again!', 'inOut');
    }
}

/**
 * Set the settings form to current values.
 */
function resetPlayerSettingsForm() {
    // Check the appropriate radio button
    $('input[name="preferred-server"]').each(function() {
        $(this).prop('checked', $(this).attr('value') == playerSettings.preferredServer);  
    });
    
    // Select owned legends
    $('.bb-legend-option').each(function() {
        if ($.inArray($(this).attr('legend'), playerSettings.ownedLegends) == -1) {
            $(this).addClass('disabled');
        }
        else {
            $(this).removeClass('disabled');
        }
    });
}

/**
 * Save the player settings and send them to the server.
 */
function savePlayerSettings() {
    // Find the checked preferred-server input
    playerSettings.preferredServer = $('input[name="preferred-server"]:checked').val();
    
    playerSettings.ownedLegends = []
    $('.bb-legend-option').each(function() {
        // If not disabled, then this legend is selected
        if (!$(this).hasClass('disabled')) {
            playerSettings.ownedLegends.push($(this).attr('legend'));
        }
    });
    
    pSocket.emit('update settings', playerSettings);
}

    
// Code below is called when player settings page is loaded

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
    savePlayerSettings();
    
    return false;
});

// Cancel button just resets
$('#bb-reset-settings').click(function() {
    resetPlayerSettingsForm();
    
    return false;
});

// Select current settings
resetPlayerSettingsForm();
    
pSocket.on('update settings', onUpdateSettings);
pSocket.on('invalid settings', onInvalidSettings);


// Called when the inner page content is removed to load a new page.
// Clean up socketIO handlers.
$('.content').on('destroy', function() {
    pSocket.off('update settings', onUpdateSettings);
    pSocket.off('invalid settings', onInvalidSettings);
});