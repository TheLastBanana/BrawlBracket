$(function () {
    var language = {
        emptyTable: 'No tournaments found'
    }
    
    var userTable = $('#bb-user-tourneys-table').DataTable({
        language: language,
        order: [[1, 'asc']],
        
        columns: [
            {
                responsivePriority: 1
            },
            {
                responsivePriority: 3
            },
            {
                responsivePriority: 4
            },
            {
                responsivePriority: 2
            }
        ]
    });
});