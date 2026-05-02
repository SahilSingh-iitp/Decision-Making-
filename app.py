import streamlit as st
from groq import Groq
import json
import uuid
from datetime import datetime
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

st.set_page_config(page_title="Decision Coach", layout="wide")

# 🔐 SECURE API KEY LOADING
api_key = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")

if not api_key:
    st.error("API key not found. Please set GROQ_API_KEY.")
    st.stop()

client = Groq(api_key=api_key)

LOG_FILE = "chat_logs.json"


def log_chat(user_input, reply, feedback=None):
    data = {
        "time": str(datetime.now()),
        "input": user_input,
        "output": reply,
        "feedback": feedback
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(data) + "\n")

def load_logs():
    if not os.path.exists(LOG_FILE):
        return []
    logs = []
    with open(LOG_FILE, "r") as f:
        for line in f:
            try:
                logs.append(json.loads(line))
            except:
                pass
    return logs


st.sidebar.title("⚙️ Menu")

page = st.sidebar.radio("Navigate", ["Chat", "Analytics", "All Chats"])

if st.sidebar.button("➕ New Chat"):
    st.session_state.messages = []
    st.rerun()


if page == "Analytics":
    st.title("📊 Analytics Dashboard")

    logs = load_logs()

    if not logs:
        st.info("No data yet.")
    else:
        total = len(logs)
        helpful = sum(1 for l in logs if l.get("feedback") == "👍 Yes")
        not_helpful = sum(1 for l in logs if l.get("feedback") == "👎 No")

        st.metric("Total Interactions", total)
        st.metric("Helpful", helpful)
        st.metric("Not Helpful", not_helpful)

    st.stop()


if page == "All Chats":
    st.title("📂 All User Chats")

    logs = load_logs()

    if not logs:
        st.info("No chats yet.")
    else:
        for log in logs[::-1]:
            st.markdown(f"### 🕒 {log['time']}")
            st.write(f"**User:** {log['input']}")
            st.write(f"**AI:** {log['output']}")
            st.write(f"**Feedback:** {log.get('feedback')}")
            st.markdown("---")

    st.stop()

st.title("🧠 Decision Coach")
st.write("Clear decisions. No nonsense.")

if "messages" not in st.session_state:
    st.session_state.messages = []

messages = st.session_state.messages

# Show chat
for msg in messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])


user_input = st.chat_input("What's your situation?")

if user_input:
    messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.write(user_input)

    system_prompt = """
You are a practical decision assistant.

Your goal:
Help the user make a clear, sensible decision.

--------------------------------
BEHAVIOR

- If situation is clear → give decision immediately
- If something important is missing → ask ONE question
- If user updates situation → adapt your answer
- Do NOT repeat blindly

--------------------------------
STYLE

- Keep answers short (2–5 lines)
- Use simple, natural language
- Be direct and practical

--------------------------------
REALITY CHECK

Before suggesting:
- Is it realistic?
- Is it under user control?

If NO → do NOT suggest it

--------------------------------
FIXED CONSTRAINTS

If something cannot change:
→ accept it
→ do not suggest changing it

--------------------------------
OUTPUT

👉 Suggested Direction: <answer>
Reason: <short explanation>
Key Factor: <main reason>
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "system", "content": system_prompt}] + messages,
            temperature=0.4
        )
        reply = response.choices[0].message.content
    except Exception as e:
        reply = "⚠️ Something went wrong."

    messages.append({"role": "assistant", "content": reply})

    with st.chat_message("assistant"):
        st.write(reply)


    feedback = st.radio(
        "Was this helpful?",
        ["👍 Yes", "👎 No"],
        key=str(uuid.uuid4())
    )

    if feedback:
        log_chat(user_input, reply, feedback)