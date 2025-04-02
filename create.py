import time
import happybase
import openai
import traceback
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ----------------------------------------------------------------------------
# 1. OpenRouter / OpenAI Setup
# ----------------------------------------------------------------------------
api_key = "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"
openai_client = openai.OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")

# ----------------------------------------------------------------------------
# 2. HBase Connection & Table Setup Functions
# ----------------------------------------------------------------------------
def connect_hbase():
    """Connect to the HBase Thrift server."""
    connection = happybase.Connection(host="localhost", port=9090)
    connection.open()
    return connection

def create_conversations_table_if_not_exists(connection, table_name="conversations"):
    """Create an HBase table to store chat messages if it doesn't exist."""
    families = {"chat": dict()}
    existing_tables = [t.decode() for t in connection.tables()]
    if table_name not in existing_tables:
        connection.create_table(table_name, families)
        print(f"Created table '{table_name}'.")
    else:
        print(f"Table '{table_name}' already exists.")