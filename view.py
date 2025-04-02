import happybase
import time

def connect_hbase():
    """Connect to the HBase Thrift server."""
    connection = happybase.Connection(host="localhost", port=9090)
    connection.open()
    return connection

def list_hbase_tables(connection):
    """List all tables in HBase."""
    tables = [t.decode() for t in connection.tables()]
    if tables:
        print("HBase Tables:")
        for table_name in tables:
            print(f"- {table_name}")
    else:
        print("No tables found in HBase.")

def view_table_content(connection, table_name, limit=5):
    """View the content of a specified HBase table."""
    try:
        table = connection.table(table_name)
        print(f"\nContent of table '{table_name}' (first {limit} rows):")
        count = 0
        for key, data in table.scan():
            print(f"Row Key: {key.decode()}")
            for column_family, columns in data.items():
                print(f"  Column Family: {column_family.decode()}")
                if hasattr(columns, 'items'):  # Check if it's a dictionary-like object
                    for column, value in columns.items():
                        print(f"    {column.decode()}: {value.decode()}")
                else:  # Handle the case where 'columns' is a single value
                    # This might need adjustment based on your actual data structure
                    print(f"    Value: {columns.decode()}")
            print("-" * 20)
            count += 1
            if count >= limit:
                break
        if count == 0:
            print("Table is empty.")
    except happybase.TableNotFoundError as e:  # Catch the exception correctly
        print(f"Error: Table '{table_name}' not found: {e}")

def create_conversations_table_if_not_exists(connection, table_name="conversations"):
    """Create an HBase table to store chat messages if it doesn't exist."""
    families = {"chat": dict()}
    existing_tables = [t.decode() for t in connection.tables()]
    if table_name not in existing_tables:
        connection.create_table(table_name, families)
        print(f"Created table '{table_name}'.")
    else:
        print(f"Table '{table_name}' already exists.")

def store_message(connection, user_id, role, content, table_name="conversations"):
    """
    Store a single message in HBase.
    Row key format: f"{user_id}::{timestamp}"
    """
    table = connection.table(table_name)
    timestamp_str = str(int(time.time() * 1000))  # millisecond timestamp
    row_key = f"{user_id}::{timestamp_str}"
    table.put(row_key, {
        b"chat:role": role.encode("utf-8"),
        b"chat:content": content.encode("utf-8")
    })

def get_conversation_history(connection, user_id, table_name="conversations"):
    """
    Retrieve all messages for a given user, sorted by row key (chronologically).
    Returns a list of dicts: [{"role": "...", "content": "..."}, ...].
    """
    table = connection.table(table_name)
    start_key = f"{user_id}::".encode("utf-8")
    stop_key  = f"{user_id};".encode("utf-8")  # simple hack: semicolon is after colon in ASCII
    conversation = []
    for key, data in table.scan(row_start=start_key, row_stop=stop_key):
        role = data.get(b"chat:role", b"").decode("utf-8")
        content = data.get(b"chat:content", b"").decode("utf-8")
        conversation.append({"role": role, "content": content})
    return conversation

if __name__ == "__main__":
    conn = connect_hbase()
    list_hbase_tables(conn)
    view_table_content(conn, "conversations") # Replace "conversations" with the table you want to view
    conn.close()