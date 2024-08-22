# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import os

import streamlit as st
from src.components import tabs
from src.components.index_pipeline import IndexPipeline
from src.enums import EnvVars
from src.functions import initialize_app
from src.graphrag_api import GraphragAPI

# Load environment variables
initialized = initialize_app()
st.session_state["initialized"] = True if initialized else False


def graphrag_app(initialized: bool):
    # main entry point for app interface
    # st.title("MOH AIM - GraphRAG Copilot")
    col1, col2 = st.columns([1, 1], vertical_alignment="bottom")
    with col1:
        st.markdown("## Welcome to ACE GraphRAG Copilot")
    with col2:
        st.image("./imgs/ACE_logo.png", width=200)
    (
        main_tab,
        prompt_gen_tab,
        prompt_edit_tab,
        index_tab,
        query_tab,
        query_history_tab,
    ) = st.tabs(
        [
            "**Intro**",
            "**1. Prompt Generation**",
            "**2. Prompt Configuration**",
            "**3. Index**",
            "**4. Query**",
            "**5. Query History**",
        ]
    )
    with main_tab:
        tabs.get_main_tab(initialized)

    # if not initialized, only main tab is displayed
    if initialized:
        # assign API request information
        COLUMN_WIDTHS = [0.275, 0.45, 0.275]
        api_url = st.session_state[EnvVars.DEPLOYMENT_URL.value]
        apim_key = st.session_state[EnvVars.APIM_SUBSCRIPTION_KEY.value]
        client = GraphragAPI(api_url, apim_key)
        indexPipe = IndexPipeline(client, COLUMN_WIDTHS)

        # display tabs
        with prompt_gen_tab:
            if "AllowCreateIndex" in st.session_state["permissions"]:
                tabs.get_prompt_generation_tab(client, COLUMN_WIDTHS)
            else:
                st.info("You do not have permission to access this tab.")
        with prompt_edit_tab:
            if "AllowCreateIndex" in st.session_state["permissions"]:
                tabs.get_prompt_configuration_tab()
            else:
                st.info("You do not have permission to access this tab.")
        with index_tab:
            if "AllowCreateIndex" in st.session_state["permissions"]:
                tabs.get_index_tab(indexPipe)
            else:
                st.info("You do not have permission to access this tab.")
        with query_tab:
            if "AllowQuery" in st.session_state["permissions"]:
                tabs.get_query_tab(client, st.session_state["graphragindexes"])
            else:
                st.info("You do not have permission to access this tab.")
        with query_history_tab:
            if "AllowQuery" in st.session_state["permissions"]:
                tabs.get_query_history_tab()
            else:
                st.info("You do not have permission to access this tab.")

    deployer_email = os.getenv("DEPLOYER_EMAIL", "deployer@email.com")

    footer = f"""
        <div class="footer">
            <p> Responses may be inaccurate; please review all responses for accuracy. Learn more about Azure OpenAI code of conduct <a href="https://learn.microsoft.com/en-us/legal/cognitive-services/openai/code-of-conduct"> here</a>. </br> For feedback, email us at <a href="mailto:{deployer_email}">{deployer_email}</a>.</p>
        </div>
    """
    st.markdown(footer, unsafe_allow_html=True)


if __name__ == "__main__" or __name__ == "__page__":
    graphrag_app(st.session_state["initialized"])
