from dotenv import load_dotenv
import streamlit as st
import os
import google.generativeai as genai

# Load environment variables from .env file
load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
use_gemini = False
if api_key:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        if "chat_session" not in st.session_state:
            st.session_state.chat_session = model.start_chat(history=[])
        use_gemini = True
    except Exception as e:
        st.warning(f"Could not initialize Gemini API; falling back to offline mode. ({e})")
        use_gemini = False
else:
    st.info("Running in offline mode — no GOOGLE_API_KEY found. The chatbot will use simple fallback replies.")


def offline_reply(user_query: str) -> str:
    """Return a simple offline reply when the API isn't available."""
    q = user_query.lower()
    if any(k in q for k in ["joke", "funny", "make me laugh"]):
        return "Why did the tomato blush? Because it saw the salad dressing! 😄"
    if any(k in q for k in ["story", "bedtime", "tell me a story"]):
        return "Once upon a time a little star learned to shine. The end. ✨"
    if any(k in q for k in ["riddle", "puzzle"]):
        return "What has keys but can't open locks? A keyboard!"
    return "I can't reach the helper brain right now, but I'd love to help — try rephrasing your question or check your API key."


def get_gemini_response(user_query):
    """Send the user's query to Gemini when available, otherwise use offline fallback."""
    try:
        if use_gemini:
            response = st.session_state.chat_session.send_message(user_query)
            return getattr(response, "text", str(response))
        else:
            return offline_reply(user_query)
    except Exception as e:
        st.error(f"An error occurred while getting the response: {e}")
        return offline_reply(user_query)


# --- Streamlit App UI ---
st.set_page_config(
    page_title="Carbon Buddy — Chat & Footprint",
    page_icon="🌍",
    layout="centered"
)

# --- Carbon-footprint themed CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="st-"] {
        font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial;
    }

    /* App background: subtle earth gradient */
    .stApp {
        background: linear-gradient(180deg, #F5FBF7 0%, #FFFFFF 60%);
        color: #073B2F;
    }

    /* Header styling */
    h1, .stTitle {
        color: #0B6E4F;
        text-align: left;
    }

    /* Chat bubbles */
    [data-testid="stChatMessage"] {
        background-color: #FFFFFF;
        border-radius: 14px;
        padding: 12px 16px;
        box-shadow: 0 6px 18px rgba(11,110,79,0.06);
        margin-bottom: 12px;
        border: 1px solid rgba(11,110,79,0.06);
    }

    /* User message: lighter green */
    [data-testid="stChatMessage"]:has(div[data-testid="stAvatarIcon-user"]) {
        background: linear-gradient(90deg, rgba(206,240,219,1) 0%, rgba(236,253,244,1) 100%);
    }

    /* Assistant message: soft earth */
    [data-testid="stChatMessage"]:has(div[data-testid="stAvatarIcon-assistant"]) {
        background: linear-gradient(90deg, rgba(255,250,240,1) 0%, rgba(245,245,240,1) 100%);
    }

    [data-testid="stChatMessageContent"] p { font-size: 15px; line-height:1.5; }

    /* Input box */
    [data-testid="stChatInput"] {
        background-color: #ffffff;
        border-radius: 12px;
        border: 1px solid rgba(11,110,79,0.12);
        padding: 8px;
    }

    /* Send button */
    button[kind="primary"] {
        background-color: #0B6E4F !important;
        color: white !important;
        border-radius: 10px !important;
        padding: 8px 12px !important;
    }

    /* Sidebar card */
    .carbon-card {
        background: linear-gradient(180deg, #FFFFFF 0%, #F7FFF6 100%);
        border-radius: 12px;
        padding: 12px;
        box-shadow: 0 4px 12px rgba(11,110,79,0.06);
        border: 1px solid rgba(11,110,79,0.06);
        margin-bottom: 12px;
    }

</style>
""", unsafe_allow_html=True)


st.title("� Carbon Buddy — Chat & Footprint")
st.write("Chat normally and also see a simple carbon footprint indicator in the sidebar. This theme uses a green/earth palette to look like a carbon-footprint tracker.")

# Initialize chat history in session state if it doesn't exist
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []


# --- Sidebar: Carbon footprint tracker widget (simple visual) ---
def compute_carbon_score(history):
    # simple deterministic estimator: baseline + messages * scale
    base = 12
    per_message = 1
    score = base + len(history) * per_message
    # clamp 0-100
    return min(max(int(score), 0), 100)

with st.sidebar:
    st.markdown("## Your Carbon Score")
    current_score = compute_carbon_score(st.session_state.chat_history)
    st.metric("Estimated footprint (kg CO₂/day)", f"{current_score}")
    st.progress(current_score / 100)
    st.markdown("""
    <div class="carbon-card">
    <strong>Tips to reduce footprint</strong>
    <ul>
      <li>Use public transport or cycle when possible 🚲</li>
      <li>Reduce meat consumption a few days a week 🥗</li>
      <li>Turn off lights and devices when not in use 💡</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

# --- Chat Input and Submission ---
user_input = st.chat_input("Ask me about math, science, history, or any educational topic!")

if user_input:
    # Add user's message to chat history and display it
    st.session_state.chat_history.append({"role": "user", "text": user_input})

    # Get Gemini's response
    with st.spinner("Thinking..."):
        gemini_response = get_gemini_response(user_input)
        st.session_state.chat_history.append({"role": "assistant", "text": gemini_response})

# --- Display Chat History ---
for message in st.session_state.chat_history:
    # Use an emoji for the avatar based on the role
    avatar = "🧑‍💻" if message["role"] == "user" else "🤖"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["text"])

