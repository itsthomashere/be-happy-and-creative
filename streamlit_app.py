import streamlit as st
import os
import openai
import uuid
from datetime import datetime
#from dotenv import load_dotenv
from sqlalchemy import text
import session_state as ss

def get_connection():
    return st.experimental_connection("digitalocean", type="sql")

def create_table_if_not_exists(session, table_name):
    session.execute(text(f'CREATE TABLE IF NOT EXISTS {table_name} (role TEXT, content TEXT);'))

def add_message_to_db(session, role, content):
    session.execute(
        text('INSERT INTO messages (role, content) VALUES (:role, :content);'),
        params=dict(role=role, content=content)
    )

openai.api_key = st.secrets["OPENAI_API_KEY"]

def setup_session_state() -> None:
    if "messages" not in st.session_state:
        st.session_state["messages"] = []

def update_session_state(role: str, content: str) -> None:
    """Append a message with role and content to st.session_state.messages."""
    st.session_state["messages"].append({
        "role": role, 
        "content": content})

def remove_duplicates(messages: list[dict[str, str]]) -> list[dict[str, str]]:
    seen = set()
    unique_messages = []
    for message in messages:
        # Create a unique identifier for each message based on its content and role
        identifier = (message["role"], message["content"])
        if identifier not in seen:
            seen.add(identifier)
            unique_messages.append(message)
    return unique_messages

def hide_st_style() -> None:
    hide_st_style = """
                <style>
                #MainMenu {visibility: hidden;}
                footer {visibility: hidden;}
                header {visibility: hidden;}
                </style>
                """
    st.markdown(hide_st_style, unsafe_allow_html=True)

def create_chat_completion(model: str, messages: list[dict[str, str]]) -> None:
    """Generate and display chat completion using OpenAI and Streamlit."""
    with st.chat_message(name="assistant", avatar=assistant_icon):
        message_placeholder = st.empty()
        full_response = ""
        for response in openai.ChatCompletion.create(
            model=model,
            messages=messages,
            stream=True,
        ):
            full_response += response.choices[0].delta.get("content", "")
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)
    return full_response

setup_session_state()
hide_st_style()

user_icon = "./icons/user_icon.png"
assistant_icon = "./icons/assistant_icon.png"

for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(name=message["role"], avatar=(assistant_icon if message["role"] == "assistant" else user_icon)):
            st.write(message["content"])

SYSTEM_PROMPT = """
I invite you to serve as both a sounding board and collaborator in exploring the potential of AI and AI tools for social advancement. Your role is to help articulate and advocate for ideas centered around leveraging AI for societal good. When I share ideas, especially those that may be brief or unclear, I'd appreciate it if you could rephrase them into more coherent and readable statements. Your advocacy should extend by elaborating on these ideas and presenting compelling arguments for their potential in driving meaningful social impact.

As an AI designed to engage in dialogue, your primary objective is to stimulate insightful discussions on utilizing AI for social upliftment and betterment. Upon receiving an idea from me, acknowledge the submission with brief commendation, restate the idea with enhanced clarity, coherence, and readability, and then pose a follow-up question to delve deeper into the idea, helping to flesh out its potential further.

After the user submits an idea, always end your response by asking if they would like to submit their response
"""

about_segment = """
Many researchers and industry leaders have warned about the potential dangers of artificial intelligence. However, through this chatbot interaction, we aim to explore the myriad ways AI tools can be harnessed for societal betterment, prosperity, and genuine social good.

Traditionally, we approach chatbots to extract information from them. In a departure from the norm, this chatbot is designed to glean insight **from you**. It stems from a fundamental belief that chatbots will never replace the profound novelty and uniqueness of the human mind, nor the remarkable ideas it can generate.

After your initial interactions with the chatbot, you will be prompted with a submit button. Should you choose to use it, you'll be adding your unique perspective to a growing reservoir of ideas shared by optimists, dreamers, and realists from around the globe.
"""

update_session_state(role="system", content=SYSTEM_PROMPT) # this is running every time something happens on streamlit

if len(st.session_state["messages"]) == 1:
    st.title("How to leverage AI for social good.")
    st.markdown(about_segment)

# User interaction
user_message = st.chat_input("Send a message")
if user_message:

    update_session_state(role="user", content=user_message)
    with st.chat_message(name="user", avatar=user_icon):
        st.write(user_message)
    
    if 'submit' not in user_message.lower():
        response = create_chat_completion(model="gpt-4", messages=st.session_state["messages"])

    st.session_state["messages"].append({"role": "assistant", "content": response})


    " --- "
if len(st.session_state.messages) > 4:
    submitted = st.form_submit_button("Save Data")
    if submitted:
        conn = get_connection()

        with conn.session as s:
            create_table_if_not_exists(s, 'messages')
            for message in ss.session_state["messages"]:
                add_message_to_db(s, message["role"], message["content"])
            s.commit()

        # Query and display the data you inserted
        messages = conn.query('select * from messages')
        st.dataframe(messages)
            st.success("Data saved!")
