# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
import os
from time import sleep

import pandas as pd
import streamlit as st

from src.auth.db import fetch_queryhistories_metadata, load_query_histories
from src.components.index_pipeline import IndexPipeline
from src.components.login_sidebar import login
from src.components.md_formatter import display_markdown_text
from src.components.prompt_configuration import (
    edit_prompts,
    prompt_editor,
    save_prompts,
)
from src.components.query import GraphQuery
from src.components.upload_files_component import upload_files
from src.enums import PromptKeys
from src.functions import generate_and_extract_prompts
from src.graphrag_api import GraphragAPI


def get_query_history_tab() -> None:
    """
    Displays the chat history for the current user.

    Returns:
        None
    """
    st.title("Past Query Histories")

    if "query_histories" not in st.session_state:
        # Load the chat histories for the current user

        try:
            list_queryhistories_metadata = fetch_queryhistories_metadata(
                "query-history", st.session_state.session_id_prefix
            )

            if not list_queryhistories_metadata:
                st.session_state.query_histories = []
                st.write("No query histories available.")
                return
            else:
                st.session_state.query_histories = list_queryhistories_metadata
        except Exception as e:
            st.error(f"Error loading blobs: {str(e)}")
            return

    if not st.session_state.query_histories:
        st.write("No query histories available.")
        return

    # selected_session = st.selectbox(
    #     "Select a session:", st.session_state.query_histories
    # )  # Append the current session to the list of sessions
    """
    df = pd.DataFrame(session_data)
    event_select_query_history_row = st.dataframe(
        df,
        key="selected_query_history_row",
        selection_mode="single-row",
        on_select="rerun",
    )

     if len(event_select_query_history_row.selection.rows) > 0:
            selectedRow = df.iloc[
                event_select_query_history_row.selection.rows[0]
            ].to_dict()
    """
    df_histories = pd.DataFrame(st.session_state.query_histories)
    event_select_query_histories = st.dataframe(
        df_histories,
        key="select_query_histories",
        selection_mode="single-row",
        on_select="rerun",
    )

    # if selected_session:
    #     session_data = load_query_histories(selected_session)
    if len(event_select_query_histories.selection.rows) > 0:
        selectedHistory = df_histories.iloc[
            event_select_query_histories.selection.rows[0]
        ].to_dict()

        selectedName = selectedHistory["name"]
        with st.expander(
            f"**blue:[Query Histories for: {selectedName}]**", expanded=True
        ):
            session_data = load_query_histories(selectedName)
            df = pd.DataFrame(session_data)
            event_select_query_history_row = st.dataframe(
                df,
                key="selected_query_history_row",
                selection_mode="single-row",
                on_select="rerun",
            )

        if len(event_select_query_history_row.selection.rows) > 0:
            selectedRow = df.iloc[
                event_select_query_history_row.selection.rows[0]
            ].to_dict()
            if "content" in selectedRow.keys() and not pd.isna(selectedRow["content"]):
                with st.expander(":blue[**Content**]", expanded=True):
                    display_markdown_text(selectedRow["content"])

            if "context" in selectedRow.keys() and not pd.isna(selectedRow["context"]):
                with st.expander(":blue[**Context**]"):
                    display_markdown_text(selectedRow["context"])

            if "reports" in selectedRow.keys() and not pd.isna(selectedRow["reports"]):
                with st.expander(":blue[**Reports**]"):
                    display_markdown_text(selectedRow["reports"])

            if "entities" in selectedRow.keys() and not pd.isna(
                selectedRow["entities"]
            ):
                with st.expander(":blue[**Entities**]"):
                    display_markdown_text(selectedRow["entities"])

            if "relationship" in selectedRow.keys() and not pd.isna(
                selectedRow["relationship"]
            ):
                with st.expander(":blue[**Relationship**]"):
                    display_markdown_text(selectedRow["relationship"])


def get_main_tab(initialized: bool) -> None:
    """
    Displays content of Main Tab
    """

    url = "https://www.microsoft.com/en-us/research/blog/graphrag-unlocking-llm-discovery-on-narrative-private-data/"
    content = f"""
    ##  Welcome to GraphRAG!
    Diving into complex information and uncovering semantic relationships utilizing generative AI has never been easier.
    Here's how you can get started with just a few clicks:
    - **PROMPT GENERATION:** (*Optional Step*)
        1. Generate fine-tuned prompts for graphrag customized to your data and domain.
        2. Select an existing Storage Container and click "Generate Prompts".
    - **PROMPT CONFIGURATION:** (*Optional Step*)
        1. Edit the generated prompts to best suit your needs.
        2. Once you are finished editing, click the "Save Prompts" button.
        3. Saving the prompts will store them for use in the follow-on Indexing step.
        4. You can also download the edited prompts for future reference.
    - **INDEXING:**
        1. Select an existing data storage container or upload data, to Index
        2. Name your index and select "Build Index" to begin building a GraphRAG Index.
        3. Check the status of the index as the job progresses.
    - **QUERYING:**
        1. Choose an existing index
        2. Specify a query type
        3. Click "Query" button to search and view insights.

    [GraphRAG]({url}) combines the power of RAG with a Graph structure, giving you insights at your fingertips.
    """
    # Display text in the gray box
    st.markdown(content, unsafe_allow_html=False)
    if not initialized:
        login()


def get_prompt_generation_tab(
    client: GraphragAPI,
    column_widths: list[float],
    num_chunks: int = 5,
) -> None:
    """
    Displays content of Prompt Generation Tab
    """
    # hard set limit to 5 files to reduce overly long processing times and to reduce over sampling errors.
    num_chunks = num_chunks if num_chunks <= 5 else 5
    _, col2, _ = st.columns(column_widths)
    with col2:
        st.header(
            "Generate Prompts (optional)",
            divider=True,
            help="Generate fine-tuned prompts for graphrag tailored to your data and domain.",
        )

        st.write(
            "Select a storage container that contains your data. GraphRAG will use this data to generate domain-specific prompts for follow-on indexing."
        )
        storage_containers = client.get_storage_container_names()

        # if no storage containers, allow user to upload files
        if isinstance(storage_containers, list) and not (any(storage_containers)):
            st.warning(
                "No existing Storage Containers found. Please upload data to continue."
            )
            uploaded = upload_files(client, key_prefix="prompts-upload-1")
            if uploaded:
                # brief pause to allow success message to display
                sleep(1.5)
                st.rerun()
        else:
            select_prompt_storage = st.selectbox(
                "Select an existing Storage Container.",
                options=[""] + storage_containers
                if isinstance(storage_containers, list)
                else [],
                key="prompt-storage",
                index=0,
            )
            disable_other_input = True if select_prompt_storage != "" else False
            with st.expander("I want to upload new data...", expanded=False):
                new_upload = upload_files(
                    client,
                    key_prefix="prompts-upload-2",
                    disable_other_input=disable_other_input,
                )
                if new_upload:
                    # brief pause to allow success message to display
                    st.session_state["new_upload"] = True
                    sleep(1.5)
                    st.rerun()
            if st.session_state["new_upload"] and not select_prompt_storage:
                st.warning(
                    "Please select the newly uploaded Storage Container to continue."
                )
            st.write(f"**Selected Storage Container:** :blue[{select_prompt_storage}]")
            triggered = st.button(
                label="Generate Prompts",
                key="prompt-generation",
                help="Select either an existing Storage Container or upload new data to enable this button.\n\
                Then, click to generate custom prompts for the LLM.",
                disabled=not select_prompt_storage,
            )
            if triggered:
                with st.spinner("Generating LLM prompts for GraphRAG..."):
                    generated = generate_and_extract_prompts(
                        client=client,
                        storage_name=select_prompt_storage,
                        limit=num_chunks,
                    )
                    if not isinstance(generated, Exception):
                        st.success(
                            "Prompts generated successfully! Move on to the next tab to configure the prompts."
                        )
                    else:
                        # assume limit parameter is too high
                        st.warning(
                            "You do not have enough data to generate prompts. Retrying with a smaller sample size."
                        )
                        while num_chunks > 1:
                            num_chunks -= 1
                            generated = generate_and_extract_prompts(
                                client=client,
                                storage_name=select_prompt_storage,
                                limit=num_chunks,
                            )
                            if not isinstance(generated, Exception):
                                st.success(
                                    "Prompts generated successfully! Move on to the next tab to configure the prompts."
                                )
                                break
                            else:
                                st.warning(f"Retrying with sample size: {num_chunks}")


def get_prompt_configuration_tab(
    download_file_name: str = "edited_prompts.zip",
) -> None:
    """
    Displays content of Prompt Configuration Tab
    """
    st.header(
        "Configure Prompts (optional)",
        divider=True,
        help="Generate fine tuned prompts for the LLM specific to your data and domain.",
    )
    prompt_values = [st.session_state[k.value] for k in PromptKeys]

    if any(prompt_values):
        prompt_editor([prompt_values[0], prompt_values[1], prompt_values[2]])
        col1, col2, col3 = st.columns(3, gap="large")
        with col1:
            clicked = st.button(
                "Save Prompts",
                help="Save the edited prompts for use with the follow-on indexing step. This button must be clicked to enable downloading the prompts.",
                type="primary",
                key="save-prompt-button",
                on_click=save_prompts,
                kwargs={"zip_file_path": download_file_name},
            )
        with col2:
            st.button(
                "Edit Prompts",
                help="Allows user to re-edit the prompts after saving.",
                type="primary",
                key="edit-prompt-button",
                on_click=edit_prompts,
            )
        with col3:
            if os.path.exists(download_file_name):
                with open(download_file_name, "rb") as fp:
                    st.download_button(
                        "Download Prompts",
                        data=fp,
                        file_name=download_file_name,
                        help="Downloads the saved prompts as a zip file containing three LLM prompts in .txt format.",
                        mime="application/zip",
                        type="primary",
                        disabled=not st.session_state["saved_prompts"],
                        key="download-prompt-button",
                    )
        if clicked:
            st.success(
                "Prompts saved successfully! Downloading prompts is now enabled."
            )


def get_index_tab(indexPipe: IndexPipeline) -> None:
    """
    Displays content of Index tab
    """
    indexPipe.storage_data_step()
    indexPipe.build_index_step()
    indexPipe.check_status_step()


def execute_query(
    query_engine: GraphQuery, query_type: str, search_index: str | list[str], query: str
) -> None:
    """
    Executes the query on the selected index
    """
    if query:
        query_engine.search(
            query_type=query_type, search_index=search_index, query=query
        )
    else:
        return st.warning("Please enter a query to search.")


def get_query_tab(client: GraphragAPI, allowed_index) -> None:
    """
    Displays content of Query Tab
    """
    with st.form("query-form"):
        gquery = GraphQuery(
            client, st.session_state.session_id, st.session_state.username
        )
        col1, col2 = st.columns(2)
        with col1:
            query_type = st.selectbox(
                "Query Type",
                ["Global Streaming", "Global", "Local"],
                key="select-query-type",
                help="Select the query type - Each yields different results of specificity. Global queries focus on the entire graph structure. Local queries focus on a set of communities (subgraphs) in the graph that are more connected to each other than they are to the rest of the graph structure and can focus on very specific entities in the graph. Global streaming is a global query that displays results as they appear live.",
            )
        with col2:
            search_indexes = client.get_index_names()
            if not any(search_indexes):
                st.warning("No indexes found. Please build an index to continue.")

            # filter indexes to only those that are complete and allowed
            filtered_indexes = [
                index for index in search_indexes if index in allowed_index
            ]

            select_index_search = st.multiselect(
                label="Index",
                options=filtered_indexes if any(filtered_indexes) else [],
                key="multiselect-index-search",
                help="Select the index(es) to query. The selected index(es) must have a complete status in order to yield query results without error. Use Check Index Status to confirm status.",
            )

        col3, col4 = st.columns([0.8, 0.2], vertical_alignment="bottom")

        with col3:
            with st.container():
                search_bar = st.text_input("Your Query", key="search-query")
                search_button = st.form_submit_button(
                    "QUERY", type="primary", use_container_width=True
                )
        with col4:
            suggest_query = st.form_submit_button(
                "Give me some ideas on what to ask", use_container_width=True
            )

        # defining a query variable enables the use of either the search bar or the search button to trigger the query
        query = st.session_state["search-query"]

        if suggest_query and any(select_index_search):
            # 'Suggest Query' Mode
            search_mode = "Local" if query_type == "Local" else "Global"
            prompt = f"""
                    Suggest 10 relevant questions about your knowledgebase.
                    Instructions:
                    - Recap the strengths of GraphRAG {search_mode} Search, particularly how it addresses the limitations of baseline RAG models.
                    - Do not provide an explanation of GraphRAG itself
                    - Ensure that the questions are varied and relevant
                    - Focus on generating a list of sample questions that are relevant to your knowledgebase that cannot be served by `baseline rag` but are suitable for `GraphRAG {search_mode} Search`.
                    """
            execute_query(
                query_engine=gquery,
                query_type=query_type,
                search_index=select_index_search,
                query=prompt,
            )
        elif len(query) > 5:
            if (search_bar and search_button) and any(select_index_search):
                st.session_state["query-context"] = f"User: {query}"

                st.write(f"You asked: \n**{query}**")

                execute_query(
                    query_engine=gquery,
                    query_type=query_type,
                    search_index=select_index_search,
                    query=query,
                )

        else:
            col1, col2 = st.columns([0.3, 0.7])
            with col1:
                if not any(select_index_search):
                    st.warning("Please select an index!")
                else:
                    st.warning(
                        "Cannot submit queries less than 6 characters in length."
                    )

    if (
        "query_context" in st.session_state
        and len(st.session_state["query_context"]) > 0
    ):
        with gquery._create_section_expander(
            f"Query History: [SESSION_ID: {st.session_state['session_id']}]"
        ):
            # st.write(
            #     gquery.format_md_text(
            #         "Double-click on content to expand text", "red", False
            #     )
            # )
            # gquery._build_st_dataframe(st.session_state["query_context"])
            df = pd.DataFrame(st.session_state["query_context"])
            event_select_query_row = st.dataframe(
                df,
                key="event_select_query_row",
                selection_mode="single-row",
                on_select="rerun",
            )

        if len(event_select_query_row.selection.rows) > 0:
            selectedRow = df.iloc[event_select_query_row.selection.rows[0]].to_dict()
            if "content" in selectedRow.keys() and not pd.isna(selectedRow["content"]):
                with st.expander(":blue[**Content**]"):
                    display_markdown_text(selectedRow["content"])

            if "context" in selectedRow.keys() and not pd.isna(selectedRow["context"]):
                with st.expander(":blue[**Context**]"):
                    display_markdown_text(selectedRow["context"])

            if "reports" in selectedRow.keys() and not pd.isna(selectedRow["reports"]):
                with st.expander(":blue[**Reports**]"):
                    display_markdown_text(selectedRow["reports"])

            if "entities" in selectedRow.keys() and not pd.isna(
                selectedRow["entities"]
            ):
                with st.expander(":blue[**Entities**]"):
                    display_markdown_text(selectedRow["entities"])

            if "relationship" in selectedRow.keys() and not pd.isna(
                selectedRow["relationship"]
            ):
                with st.expander(":blue[**Relationship**]"):
                    display_markdown_text(selectedRow["relationship"])
