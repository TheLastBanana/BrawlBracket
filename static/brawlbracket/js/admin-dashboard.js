// Handle for table refresh interval
var tableRefresh;

// Custom sorting function to put empty elements at the bottom
$.extend($.fn.dataTableExt.oSort, {
    'anti-empty-asc': function (a, b) {
        if (a == '') return 1;
        if (b == '') return -1;
        
        return a.localeCompare(b);
    },
  
    'anti-empty-desc': function (a, b) {
        if (a == '') return 1;
        if (b == '') return -1;
        
        return b.localeCompare(a);
    }
});

/**
 * Return a formatted display string for a lobby's status.
 * @param {json} data - The cell data received from the DataTable.
 */
function formatLobbyStatus(data) {
    var cell = $(this);
    var color = '';
    var icon = '';
    
    switch (data.state) {
        case 'waitingForMatch':
            icon = 'clock-o';
            color = 'yellow';
            break;
            
        case 'waitingForPlayers':
            icon = 'user-times';
            color = 'yellow';
            break;
            
        case 'inGame':
            icon = 'play';
            color = 'green';
            break;
            
        default:
            // Assume setting up lobby
            icon = 'cog';
            color = 'aqua';
            break;
    }
    
    return '<span class="text-' +
           color +
           '"><i class="fa fa-fw fa-' +
           icon +
           '"></i> ' +
           data.display +
           '</span>';
}

/**
 * Return a formatted display string for a user's status.
 * @param {json} data - The cell data received from the DataTable.
 */
function formatUserStatus(data) {
    var cell = $(this);
    var color = '';
    var icon = '';
        
    switch (data.status) {
        case 'waiting':
            icon = 'clock-o';
            color = 'yellow';
            break;
            
        case 'waitingList':
            icon = 'list-alt';
            color = 'muted';
            break;
            
        case 'eliminated':
            icon = 'times';
            color = 'red';
            break;
            
        case 'playing':
            icon = 'play';
            color = 'green';
            break;
            
        default:
            // Assume setting up lobby
            icon = 'cog';
            color = 'info';
            break;
    }
    
    return '<span class="text-' +
           color +
           '"><i class="fa fa-fw fa-' +
           icon +
           '"></i> ' +
           data.display +
           '</span>';
}

/**
 * Return a formatted display string for a user's online/offline status.
 * @param {json} data - The cell data received from the DataTable.
 */
function formatUserOnline(data) {
    var labelType;
    
    switch (data) {
        case 'Online':
            labelType = 'success';
            break;
        
        case 'Offline':
            labelType = 'danger';
            break;
            
        default:
            labelType = 'warning';
            break;
    }
    
    return '<span class="label label-' + labelType + '">' + data + '</span>';
}

$(function () {
    // Set up the lobby table
    var lobbyTable = $('#bb-lobby-table').DataTable({
        // Sort by status, then by id
        'order': [
            [5, 'asc'],
            [0, 'asc']
        ],
        
        'ajax': '/app-data/lobbies/' + tourneyName,
        
        'columns': [
            { 'data': 'id' },
            
            {
                'data': 'p1Name',
                'type': 'anti-empty'
            },
            
            {
                'data': 'p2Name',
                'type': 'anti-empty'
            },
            
            { 'data': 'score' },
            
            {
                'data': 'room',
                'type': 'anti-empty'
            },
            
            // Special rendering for time formatting
            { 
                'data': 'startTime',
                'render': function (data, type, full, meta) {
                    switch (type) {
                        case 'type':
                            return 'date';
                        
                        default:
                            return data == ''
                                   ? 'N/A'
                                   : getTimerString(data);
                    }
                }
            },
            
            // Special rendering for colors and icons
            { 
                'data': 'status',
                'render': function (data, type, full, meta) {
                    switch (type) {
                        case 'display':
                            return formatLobbyStatus(data);
                        
                        case 'sort':
                            return data.sort;
                            
                        case 'type':
                            return 'string';
                        
                        default:
                            return data.display;
                    }
                }
            }
        ]
    });
    
    // Set up the user table
    var userTable = $('#bb-user-table').DataTable({
        'ajax': '/app-data/users/' + tourneyName,
        
        'columns': [
            { 'data': 'seed' },
            { 'data': 'name' },
            
            // Special rendering for label coloring
            {
                'data': 'online',
                'render': function(data, type, full, meta) {
                    switch (type) {
                        case 'display':
                            return formatUserOnline(data);
                            
                        case 'type':
                            return 'string';
                        
                        default:
                            return data;
                    }
                }
            },
            
            // Special rendering for colors and icons
            {
                'data': 'status',
                'render': function(data, type, full, meta) {
                    switch (type) {
                        case 'display':
                            return formatUserStatus(data);
                            
                        case 'type':
                            return 'string';
                        
                        default:
                            return data.display;
                    }
                }
            }
        ]
    });
    
    // Refresh tables periodically
    tableRefresh = setInterval(function() {
        lobbyTable.ajax.reload(null, false); // Don't reset paging
        userTable.ajax.reload(null, false);
        
        console.log('reload');
    }, 5000);
    
    // Called when the inner page content is removed to load a new page.
    $('.content').on('destroy', function() {
        window.clearInterval(tableRefresh);
    });
});