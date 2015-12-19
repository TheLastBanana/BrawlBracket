import db_wrapper

def init_example_db():
    db = db_wrapper.DBWrapper('dbname', filepath='.')
    
    if not db.table_exists('test_table'):
        # https://www.sqlite.org/datatype3.html
        db.create_table(
            'tablename',
            ['field1', 'field2'],
            ['INTEGER', 'TEXT'],
            'field1') # primary field
            
        assert(db.table_exists('tablename'))
        
        db.insert_values('tablename', [('1', 'test'),
                                       (2, 'test2'), 
                                       (3, 'test3')])

        db.delete_values('tablename', 'field2 = 3')
