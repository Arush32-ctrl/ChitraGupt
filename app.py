import streamlit as st
import sqlite3
from datetime import datetime

# ऐप का नाम और मोबाइल लेआउट सेट करना
st.set_page_config(page_title="Chitragupt AI", page_icon="🤖", layout="centered")

# --- डेटाबेस सेटअप (ai_memory.db) ---
def init_db():
    conn = sqlite3.connect("ai_memory.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT,
            message TEXT,
            timestamp TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_message(sender, message):
    conn = sqlite3.connect("ai_memory.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO chat_history (sender, message, timestamp) VALUES (?, ?, ?)", 
                   (sender, message, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def load_messages():
    conn = sqlite3.connect("ai_memory.db")
    cursor = conn.cursor()
    cursor.execute("SELECT sender, message FROM chat_history ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()
    return [{"role": row[0], "content": row[1]} for row in rows]

# डेटाबेस चालू करें
init_db()

# --- ऐप का मुख्य इंटरफ़ेस (UI) ---
st.title("🤖 Chitragupt AI")
st.caption("आपका अपना पर्सनल एआई असिस्टेंट")

# चैट हिस्ट्री लोड करना
if "messages" not in st.session_state:
    st.session_state.messages = load_messages()

# पुरानी चैट को स्क्रीन पर दिखाना
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# यूज़र से इनपुट लेना
if user_input := st.chat_input("Chitragupt से कुछ पूछें..."):
    # 1. यूज़र का मैसेज स्क्रीन पर दिखाएं और सेव करें
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    save_message("user", user_input)
    
    # 2. एआई का रिस्पॉन्स
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        
        # यहाँ आपका डिफ़ॉल्ट रिस्पॉन्स है
        ai_response = f"नमस्ते! मैं चित्रगुप्त हूँ। आपकी पायथन स्क्रिप्ट अब मोबाइल ऐप इंटरफ़ेस पर लाइव काम कर रही है!" 
        
        response_placeholder.markdown(ai_response)
        
    # 3. एआई का मैसेज सेव करें
    st.session_state.messages.append({"role": "assistant", "content": ai_response})
    save_message("assistant", ai_response)
