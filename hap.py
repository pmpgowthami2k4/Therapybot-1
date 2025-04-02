import happybase

def connect_hbase():
    """Connect to the HBase Thrift server."""
    connection = happybase.Connection('localhost', port=9090)
    connection.open()
    return connection

def create_table_if_not_exists(connection, table_name='users'):
    """Create the table if it does not exist, with one column family 'login'."""
    families = {'login': dict()}
    # Get existing tables as decoded strings
    existing_tables = [t.decode() for t in connection.tables()]
    if table_name not in existing_tables:
        connection.create_table(table_name, families)
        print(f"Created table '{table_name}'.")
    else:
        print(f"Table '{table_name}' already exists.")

def insert_sample_users(connection, table_name='users'):
    """Insert sample user records into the table."""
    table = connection.table(table_name)
    # Insert sample users; note the row key should be unique
    table.put('user_1', {
        'login:username': 'john_doe',
        'login:password': 'hashed_password1',  # In production, use a secure hash!
        'login:email': 'john@example.com'
    })
    table.put('user_2', {
        'login:username': 'john_doe',
        'login:password': 'hashed_password2',
        'login:email': 'john2@example.com'
    })
    table.put('user_3', {
        'login:username': 'jane_doe',
        'login:password': 'hashed_password3',
        'login:email': 'jane@example.com'
    })
    print("Inserted sample user records.")

def query_users_by_username(connection, username, table_name='users'):
    """
    Retrieve all user records where the login:username matches the provided value.
    Uses an HBase SingleColumnValueFilter.
    """
    table = connection.table(table_name)
    # Build filter string: family and qualifier are 'login' and 'username'
    filter_str = f"SingleColumnValueFilter('login', 'username', =, 'binary:{username}')"
    
    results = []
    for key, data in table.scan(filter=filter_str):
        user_info = {k.decode('utf-8'): v.decode('utf-8') for k, v in data.items()}
        user_info['row_key'] = key.decode('utf-8')
        results.append(user_info)
    return results

def update_user_email(connection, row_key, new_email, table_name='users'):
    """Update the email of the user identified by row_key."""
    table = connection.table(table_name)
    table.put(row_key, {'login:email': new_email})
    print(f"Updated email for user '{row_key}' to {new_email}.")

def main():
    connection = connect_hbase()
    table_name = 'users'
    
    # Create the table and insert sample users if needed
    create_table_if_not_exists(connection, table_name)
    insert_sample_users(connection, table_name)
    
    # Query for users with a specific login username
    username_to_query = 'john_doe'
    users = query_users_by_username(connection, username_to_query, table_name)
    print(f"\nUsers with login username '{username_to_query}':")
    for user in users:
        print(user)
    
    # Example: Update email for the first user found (if any)
    if users:
        first_user_key = users[0]['row_key']
        update_user_email(connection, first_user_key, 'new_email@example.com', table_name)
        
        # Query again to show updated data
        updated_user = query_users_by_username(connection, username_to_query, table_name)
        print(f"\nUpdated user data for username '{username_to_query}':")
        for user in updated_user:
            print(user)
    
    connection.close()

if __name__ == '__main__':
    main()


'''

& "C:/Program Files/Python312/python.exe" -m pip install kafka-python happybase
'''