import firebase_admin
from firebase_admin import credentials, firestore

# Load Firebase credentials
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

# Initialize Firestore
db = firestore.client()

# ✅ Function to Store Messages
def store_message(user_id, message, response):
    doc_ref = db.collection("conversations").add({
        "userId": user_id,
        "message": message,
        "response": response
    })
    print("✅ Message stored in Firestore!")

# ✅ Function to Retrieve Messages
def get_user_messages(user_id):
    messages_ref = db.collection("conversations").where("userId", "==", user_id).stream()
    return [doc.to_dict() for doc in messages_ref]
