import streamlit as st
import os
import openai
import uuid
from datetime import datetime
#from dotenv import load_dotenv

load_dotenv()
#openai.api_key = os.environ.get("OPENAI_API_KEY")
openai.api_key = st.secrets["OPENAI_API_KEY"]

def setup_session_state() -> None:
    if "messages" not in st.session_state:
        st.session_state["messages"] = []

def update_session_state(role: str, content: str) -> None:
    """Append a message with role and content to st.session_state.messages."""
    st.session_state["messages"].append({
        "role": role, 
        "content": content})


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
    with st.chat_message(name="assistant", avatar="🤔"):
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

user_icon = "🟡"
assistant_icon = "🟣"

for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(name=message["role"], avatar=(assistant_icon if message["role"] == "assistant" else user_icon)):
            st.write(message["content"])

system_prompt = """You are an AI designed to ask the user questions in the hope of extracting insight from the 
user on how to leverage AI for social good and the uplifting and betterment of society. You are expecting
the user to provide you with an idea. Please encourage the user to submit something, and once they share an idea with you, 
briefly commend them on their great idea, briefly restate their idea with greater clarity, coherence and readability, and then 
promptly ask the user a follow-up question to help them expand upon that idea. 
"""

update_session_state(role="system", content=system_prompt)
# User interaction
user_message = st.chat_input("Send a message")
if user_message:
    update_session_state(role="user", content=user_message)
    with st.chat_message(name="user"):
        st.write(user_message)
    
    response = create_chat_completion(model="gpt-4", messages=st.session_state["messages"])

    st.session_state["messages"].append({"role": "assistant", "content": response})


    " --- "
if len(st.session_state["messages"]) > 2:
    with st.form("my_form"):
        submitted = st.form_submit_button("Save Data")
        if submitted:
            st.session_state["uuid"] = str(uuid.uuid4())
            st.markdown(st.session_state["uuid"])
            st.markdown(st.session_state["messages"])
            st.success("Data saved!")

