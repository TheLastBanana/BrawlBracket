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
    $('#bb-match-table').DataTable({
        'columnDefs': [
            { 'type': 'anti-empty', 'targets': [1, 2] }
        ]
    });
});