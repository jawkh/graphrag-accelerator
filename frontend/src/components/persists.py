import streamlit as st


def store_value(key):
    st.session_state[key] = st.session_state["_" + key]


def load_value(key):
    if key in st.session_state:
        st.session_state["_" + key] = st.session_state[key]
