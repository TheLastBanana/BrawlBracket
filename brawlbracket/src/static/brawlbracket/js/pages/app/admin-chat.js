// Handle for table refresh interval
var tableRefresh;

// The user table
var adminChatUserTable;

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
 * Get the active chats (i.e. ones to display).
 *
 * @return {array}  The list of chat IDs.
 */
function getActiveAdminChats() {
    var chats = localStorage.getItem('activeAdminChats');
    if (chats) {
        return JSON.parse(chats);
    } else {
        return [];
    }
}

/**
 * Add a player's chat to the active admin chats.
 *
 * @param {string}  name    - The player's name.
 * @param {string}  chatId  - The chat's unique id.
 */
function addAdminChat(name, chatId) {
    var chats = getActiveAdminChats();
    chats.push(chatId);
    
    localStorage.setItem('activeAdminChats', JSON.stringify(chats));
    
    renderAdminChats();
}

/**
 * Render the admin chats.
 */
function renderAdminChats() {
    var chats = getActiveAdminChats();
    var userData = adminChatUserTable.ajax.json();
    
    // Match up usernames with chat ids
    var namedChats = [];
    for (var i = 0; i < chats.length; ++i) {
        for (var j = 0; j < userData.data.length; ++j) {
            if (chats[i] == userData.data[j].chatId) {
                namedChats.push({
                    name: userData.data[j].name,
                    id: chats[i]
                });
                continue;
            }
        }
    }
    
    ReactDOM.render(
        React.createElement(AdminChat,
            {
              socket: chatSocket,
              chatCache: chatCache,
              userId: userId,
              chats: namedChats
            }
        ),
        $('#bb-admin-chats').get(0)
    );
}

/**
 * Initialize the admin chat.
 */
function initAdminChat() {
    // Set up the team table
    adminChatUserTable = $('#bb-chat-users-table').DataTable({
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
    
    adminChatUserTable.on('click', 'button.open-chat', function() {
        var data = adminChatUserTable.row($(this).parents('tr')).data();
        addAdminChat(data.name, data.chatId);
    });
    
    // Render admin chats once the table data has arrived
    adminChatUserTable.on('xhr', function() {
        renderAdminChats();
    });
    
    // Refresh table periodically
    tableRefresh = setInterval(function() {
        //userTable.ajax.reload(null, false); // Don't reset paging
    }, 5000);
    
    // Called when the inner page content is removed to load a new page.
    $('.content').on('destroy', function() {
        window.clearInterval(tableRefresh);
    });
}