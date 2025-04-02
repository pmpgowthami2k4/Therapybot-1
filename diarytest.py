import os
import uuid
import json
import base64
from datetime import datetime

import happybase
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

class DiaryHBaseManager:
    def _init_(self, host='localhost', port=9090, retry_count=3):
        """
        Initialize HBase connection with retry mechanism
        
        :param host: HBase Thrift server host
        :param port: HBase Thrift server port
        :param retry_count: Number of connection retry attempts
        """
        self.host = host
        self.port = port
        self.retry_count = retry_count
        self.connection = None
        self.table_name = 'diary_entries'
        
        self.connect()
        self.create_table_if_not_exists()
    
    def connect(self):
        """
        Establish connection to HBase with retry logic
        """
        for attempt in range(self.retry_count):
            try:
                self.connection = happybase.Connection(host=self.host, port=self.port)
                print(f"Successfully connected to HBase on attempt {attempt + 1}")
                return
            except Exception as e:
                print(f"Connection attempt {attempt + 1} failed: {e}")
                if attempt == self.retry_count - 1:
                    raise RuntimeError(f"Failed to connect to HBase after {self.retry_count} attempts")
                import time
                time.sleep(5)  # Wait 5 seconds before retrying
    
    def create_table_if_not_exists(self):
        """
        Create the diary entries table in HBase if it doesn't exist
        """
        try:
            # List existing tables
            existing_tables = self.connection.tables()
            
            # Check if our table exists
            if self.table_name.encode() not in existing_tables:
                # Create table with column families
                self.connection.create_table(
                    self.table_name, 
                    {
                        'info': dict(),      # Basic entry information
                        'content': dict(),   # Entry content and details
                        'metadata': dict()   # Additional metadata
                    }
                )
                print(f"Created table: {self.table_name}")
            else:
                print(f"Table {self.table_name} already exists")
        except Exception as e:
            print(f"Error creating table: {e}")
    
    def save_entry(self, entry_data):
        """
        Save a diary entry to HBase
        
        :param entry_data: Dictionary containing entry details
        :return: Entry ID
        """
        try:
            # Generate a unique row key
            row_key = str(uuid.uuid4())
            
            # Open table connection
            table = self.connection.table(self.table_name)
            
            # Prepare data for HBase storage
            data = {
                b'info:id': row_key.encode(),
                b'info:title': entry_data['title'].encode(),
                b'info:date': entry_data['date'].encode(),
                b'content:text': entry_data['content'].encode(),
                b'metadata:created_at': entry_data.get('createdAt', datetime.utcnow().isoformat()).encode()
            }
            
            # Store images as JSON in metadata
            if entry_data.get('images'):
                data[b'metadata:images'] = json.dumps(entry_data['images']).encode()
            
            # Put data into HBase
            table.put(row_key.encode(), data)
            
            return row_key
        
        except Exception as e:
            print(f"Error saving entry to HBase: {e}")
            return None
    
    def get_entries(self):
        """
        Retrieve all diary entries from HBase
        
        :return: List of diary entries
        """
        try:
            table = self.connection.table(self.table_name)
            entries = []
            
            for key, data in table.scan():
                entry = {
                    'id': key.decode(),
                    'title': data.get(b'info:title', b'').decode(),
                    'date': data.get(b'info:date', b'').decode(),
                    'content': data.get(b'content:text', b'').decode(),
                    'createdAt': data.get(b'metadata:created_at', b'').decode(),
                    'images': json.loads(data.get(b'metadata:images', b'[]').decode())
                }
                entries.append(entry)
            
            # Sort entries by date (newest first)
            return sorted(entries, key=lambda x: x['date'], reverse=True)
        
        except Exception as e:
            print(f"Error retrieving entries from HBase: {e}")
            return []
    
    def get_entry_by_id(self, entry_id):
        """
        Retrieve a specific diary entry by ID
        
        :param entry_id: Entry ID to retrieve
        :return: Dictionary of entry details or None
        """
        try:
            table = self.connection.table(self.table_name)
            row = table.row(entry_id.encode())
            
            if not row:
                return None
            
            entry = {
                'id': entry_id,
                'title': row.get(b'info:title', b'').decode(),
                'date': row.get(b'info:date', b'').decode(),
                'content': row.get(b'content:text', b'').decode(),
                'createdAt': row.get(b'metadata:created_at', b'').decode(),
                'images': json.loads(row.get(b'metadata:images', b'[]').decode())
            }
            
            return entry
        
        except Exception as e:
            print(f"Error retrieving entry from HBase: {e}")
            return None
    
    def close(self):
        """
        Close HBase connection
        """
        if self.connection:
            self.connection.close()

def create_app():
    """
    Create and configure Flask application
    """
    app = Flask(__name__)
    CORS(app)  # Enable CORS for all routes

    # Configuration
    UPLOAD_FOLDER = 'uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

    # Ensure upload directory exists
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    # Initialize HBase Manager
    hbase_manager = DiaryHBaseManager(host='localhost', port=9090)

    def allowed_file(filename):
        """Check if the file has an allowed extension."""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    def generate_unique_filename(filename):
        """Generate a unique filename to prevent overwrites."""
        ext = filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4()}.{ext}"
        return unique_filename

    @app.route('/api/entries', methods=['GET'])
    def get_entries():
        """Retrieve all diary entries."""
        entries = hbase_manager.get_entries()
        return jsonify(entries)

    @app.route('/api/entries', methods=['POST'])
    def create_entry():
        """Create a new diary entry."""
        data = request.json

        # Validate required fields
        if not all(key in data for key in ['title', 'content', 'date']):
            return jsonify({"error": "Missing required fields"}), 400

        # Process uploaded images
        images = data.get('images', [])
        processed_images = []

        for img_data in images:
            # Skip if not a base64 data URL
            if not img_data.startswith('data:image'):
                continue

            # Extract file extension and decode
            header, encoded = img_data.split(",", 1)
            ext = header.split(';')[0].split('/')[1]
            img_data = base64.b64decode(encoded)

            # Generate unique filename
            filename = f"{uuid.uuid4()}.{ext}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            # Save file
            with open(filepath, 'wb') as f:
                f.write(img_data)

            processed_images.append(f"/uploads/{filename}")

        # Prepare entry data
        entry = {
            'title': data['title'],
            'content': data['content'],
            'date': data['date'],
            'images': processed_images,
            'createdAt': datetime.utcnow().isoformat()
        }

        # Save to HBase
        entry_id = hbase_manager.save_entry(entry)
        
        if entry_id:
            entry['id'] = entry_id
            return jsonify(entry), 201
        else:
            return jsonify({"error": "Failed to save entry"}), 500

    @app.route('/api/entries/<entry_id>', methods=['GET'])
    def get_entry(entry_id):
        """Retrieve a specific diary entry."""
        entry = hbase_manager.get_entry_by_id(entry_id)
        if entry:
            return jsonify(entry)
        return jsonify({"error": "Entry not found"}), 404

    @app.route('/uploads/<filename>')
    def uploaded_file(filename):
        """Serve uploaded files."""
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    # Error Handlers
    @app.errorhandler(413)
    def request_entity_too_large(error):
        return jsonify({"error": "File too large"}), 413

    # Cleanup HBase connection on app shutdown
    @app.teardown_appcontext
    def close_hbase_connection(exception=None):
        hbase_manager.close()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)