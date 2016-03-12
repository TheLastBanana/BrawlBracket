$(function () {
    var language = {
        emptyTable: 'No tournaments found'
    }
    
    var userTable = $('#bb-user-tourneys-table').DataTable({
        language: language,
        order: [[1, 'asc']],
        
        columns: [
            {
                orderable: false,
                defaultContent: ''
            },
            {},
            {},
            {},
            {}
        ]
    });
});