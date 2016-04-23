// Handle for table refresh interval
var tableRefresh;

/**
 * Return a formatted display string for a user's name, including a link to open their chat.
 * @param {json} fullData - The row data received from the DataTable.
 */
function formatUserName(fullData) {
    return '<button class="btn btn-sm btn-primary open-chat" style="width: 100%;">' + fullData.name + '</button>';
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

/**
 * Initialize the admin chat.
 */
function initAdminChat () {
    ReactDOM.render(
        React.createElement(AdminChat,
            {
              socket: chatSocket,
              chatCache: chatCache,
              userId: userId,
              chatIds: [{id: '4edfadd0-0822-11e6-a5c1-60a44c2cdcf6', name: '[k☠ʞ] TheLastBanana'}]
            }
        ),
        $('#bb-admin-chats').get(0)
    );
    
    // Set up the team table
    var userTable = $('#bb-chat-users-table').DataTable({
        'ajax': '/app-data/users/' + tourneyName,
        
        'columns': [
            {
                'data': 'name',
                'render': function(data, type, full, meta) {
                    switch (type) {
                        case 'display':
                            return formatUserName(full);
                        
                        case 'type':
                            return 'string';
                            
                        default:
                            return data;
                    }
                }
            },
            {
                'data': 'team'
            },
            
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
            }
        ]
    });
    
    userTable.on('click', 'button.open-chat', function() {
        var data = userTable.row($(this).parents('tr')).data();
        alert(data.id);
    })
    
    // When tabs are switched, we need to recalculate the responsize table's width since it was hidden before
    $('#bb-admin-dash-tables').on('shown.bs.tab', function(e) {
        $(this).find('.table').DataTable().responsive.recalc();
    });
    
    // Refresh tables periodically
    tableRefresh = setInterval(function() {
        //userTable.ajax.reload(null, false); // Don't reset paging
    }, 5000);
    
    // Called when the inner page content is removed to load a new page.
    $('.content').on('destroy', function() {
        window.clearInterval(tableRefresh);
    });
}