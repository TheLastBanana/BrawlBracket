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
            
        case 'complete':
            icon = 'check';
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
 * Return a formatted display string for a team's status.
 * @param {json} data - The cell data received from the DataTable.
 */
function formatTeamStatus(data) {
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
 * Return a formatted display string for a team's online/offline status.
 * @param {json} data - The cell data received from the DataTable.
 */
function formatTeamOnline(data) {
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

/**
 * Initialize the admin dashboard.
 */
 function initAdminDashboard () {
    // Set up the lobby table
    var lobbyTable = $('#bb-lobby-table').DataTable({
        // Sort by status, then by id
        'order': [
            [6, 'asc'],
            [0, 'asc']
        ],
        
        'ajax': '/app-data/lobbies/' + tourneyName,
        
        'columns': [
            {
                'data': 'id',
                'responsivePriority': 1
            },
            
            {
                'data': 't1Name',
                'type': 'anti-empty',
                'responsivePriority': 3
            },
            
            {
                'data': 't2Name',
                'type': 'anti-empty',
                'responsivePriority': 3
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
                                   : getTimerString(new Date(new Date() - new Date(data)));
                    }
                },
                'responsivePriority': 4
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
                },
                'responsivePriority': 2
            }
        ]
    });
    
    // Set up the team table
    var teamTable = $('#bb-team-table').DataTable({
        'ajax': '/app-data/teams/' + tourneyName,
        
        'columns': [
            { 'data': 'seed' },
            { 'data': 'name' },
            
            // Special rendering for label coloring
            {
                'data': 'online',
                'render': function(data, type, full, meta) {
                    switch (type) {
                        case 'display':
                            return formatTeamOnline(data);
                            
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
                            return formatTeamStatus(data);
                            
                        case 'type':
                            return 'string';
                        
                        default:
                            return data.display;
                    }
                }
            }
        ]
    });
    
    // When tabs are switched, we need to recalculate the responsize table's width since it was hidden before
    $('#bb-admin-dash-tables').on('shown.bs.tab', function(e) {
        $(this).find('.table').DataTable().responsive.recalc();
    });
    
    // Refresh tables periodically
    tableRefresh = setInterval(function() {
        lobbyTable.ajax.reload(null, false); // Don't reset paging
        teamTable.ajax.reload(null, false);
    }, 5000);
    
    // Called when the inner page content is removed to load a new page.
    $('.content').on('destroy', function() {
        window.clearInterval(tableRefresh);
    });
}