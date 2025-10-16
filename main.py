# main.py
import os
import streamlit as st
from modules.master_agent import MasterAgent

st.set_page_config(page_title="PCORnet Chat + ICD", layout="wide")

# Initialize session state
if "agent" not in st.session_state:
    st.session_state.agent = MasterAgent()

if "response" not in st.session_state:
    st.session_state.response = None

st.title("PCORnet Chat / ICD Assistant")

# Dropdown to select agent type
agent_type = st.selectbox("Select Agent", ["Chat", "ICD"])

# Clear previous response when agent type changes
if "prev_agent" not in st.session_state or st.session_state.prev_agent != agent_type:
    st.session_state.response = None
    st.session_state.prev_agent = agent_type

# User input
prompt = st.text_input("Enter your query:")

# Send button
if st.button("Send") and prompt:
    st.session_state.response = st.session_state.agent.chat(prompt, agent_type)

# Display response
if st.session_state.response:
    if agent_type.lower() == "icd":
        st.json(st.session_state.response)
    else:
        st.text(st.session_state.response)
