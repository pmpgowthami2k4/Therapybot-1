// Import necessary Firebase modules for Firebase v9+
import { initializeApp } from "https://www.gstatic.com/firebasejs/9.6.1/firebase-app.js";
import { getFirestore, collection, addDoc, deleteDoc, doc, serverTimestamp, query, orderBy, onSnapshot } from "https://www.gstatic.com/firebasejs/9.6.1/firebase-firestore.js";

// Firebase Configuration
const firebaseConfig = {
    apiKey: "AIzaSyDliF9vwl18NBTrYSgMxBrTJcinzfphg3g",
    authDomain: "therapybot-22b03.firebaseapp.com",
    projectId: "therapybot-22b03",
    storageBucket: "therapybot-22b03.appspot.com", // Updated storage bucket
    messagingSenderId: "356471372007",
    appId: "1:356471372007:web:96f9485d4e58e60ef5ca42"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Firestore
const db = getFirestore(app);
console.log("🔥 Firestore initialized successfully!");

// Save Entry Function
function saveEntry() {
    let title = document.getElementById("title").value;
    let content = document.getElementById("content").value;

    if (title.trim() === "" || content.trim() === "") {
        alert("Title and content cannot be empty!");
        return;
    }

    addDoc(collection(db, "diary"), {
        title: title,
        content: content,
        timestamp: serverTimestamp()
    })
    .then(() => {
        console.log("✅ Entry saved!");
        document.getElementById("title").value = "";
        document.getElementById("content").value = "";
        loadEntries();
    })
    .catch(error => {
        console.error("❌ Error saving entry:", error);
    });
}

// Load Entries Function
function loadEntries() {
    const entriesContainer = document.getElementById("entries-container");
    entriesContainer.innerHTML = ""; // Clear existing entries

    // Query Firestore for the entries
    const q = query(collection(db, "diary"), orderBy("timestamp", "desc"));

    onSnapshot(q, snapshot => {
        snapshot.forEach(doc => {
            let entry = doc.data();
            entriesContainer.innerHTML += `
                <div class="entry-card">
                    <h3>${entry.title}</h3>
                    <p>${entry.content}</p>
                    <button onclick="deleteEntry('${doc.id}')">🗑 Delete</button>
                </div>`;
        });
    });
}

// Delete Entry Function
function deleteEntry(id) {
    deleteDoc(doc(db, "diary", id))
    .then(() => {
        console.log("✅ Entry deleted");
        loadEntries();
    })
    .catch(error => {
        console.error("❌ Error deleting entry:", error);
    });
}

// Event listener for save button
document.addEventListener("DOMContentLoaded", function() {
    // Add event listener to save button
    document.getElementById("saveButton").addEventListener("click", saveEntry);

    // Load entries on page load
    loadEntries();
});




