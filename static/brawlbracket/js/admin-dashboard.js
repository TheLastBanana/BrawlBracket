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

$(function() {
    var lobbyTable = $('#bb-lobby-table');
    
    // Color and add icons for lobby status
    lobbyTable.find('tbody tr td:nth-child(6)').each(function() {
        var cell = $(this);
        var status = cell.attr('status');
        var color = '';
        var icon = '';
        
        switch (status) {
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
        
        cell.prepend('<i class="fa fa-fw fa-' + icon + '"></i> ');
        cell.wrapInner('<span class="text-' + color + '"></span>');
    });
    
    lobbyTable.DataTable({
        'columnDefs': [
            { 'type': 'anti-empty', 'targets': [1, 2, 4] }
        ]
    });
    
    
    var userTable = $('#bb-user-table');
    
    // Color online/offline
    userTable.find('tbody tr td:nth-child(3)').each(function() {
        var cell = $(this);
        var labelType;
        
        switch (cell.text()) {
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
        
        cell.wrapInner('<span class="label label-' + labelType + '"></span>');
    });
    
    // Color and add icons for user status
    userTable.find('tbody tr td:nth-child(4)').each(function() {
        var cell = $(this);
        var status = cell.attr('status');
        var color = '';
        var icon = '';
        
        switch (status) {
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
        
        cell.prepend('<i class="fa fa-fw fa-' + icon + '"></i> ');
        cell.wrapInner('<span class="text-' + color + '"></span>');
    });
    
    userTable.DataTable();
});