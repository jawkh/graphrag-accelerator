import ast

import streamlit as st


def display_markdown_text(text: str):
    if is_valid_list_of_dicts(text):
        display_pythonListDict_as_markdown(ast.literal_eval(text))
    else:
        st.markdown(text)


def display_pythonListDict_as_markdown(listDict):
    for item in listDict:
        # Process common fields that might exist in all dictionary types
        if "title" in item:
            st.markdown(f"### {item['title']}")

        if "entity" in item:
            st.markdown(f"**Entity:** {item['entity']}")

        if "rank" in item:
            st.markdown(f"**Rank:** {item['rank']}")

        if "in_context" in item:
            st.markdown(f"**In Context:** {item['in_context']}")

        if "id" in item:
            st.markdown(f"**ID:** {item['id']}")

        if "index_id" in item:
            st.markdown(f"**Index ID:** {item['index_id']}")

        if "index_name" in item:
            st.markdown(f"**Index Name:** {item['index_name']}")

        if "number of relationships" in item:
            st.markdown(
                f"**Number of Relationships:** {item['number of relationships']}"
            )

        if "source" in item:
            st.markdown(f"**Source:** {item['source']}")

        if "target" in item:
            st.markdown(f"**Target:** {item['target']}")

        if "weight" in item:
            st.markdown(f"**Weight:** {item['weight']}")

        if "links" in item:
            st.markdown(f"**Links:** {item['links']}")

        if "content" in item:
            st.markdown(item["content"])

        if "description" in item:
            st.markdown(item["description"])

        # Add a horizontal line to separate different entries, only if any field was displayed
        if any(
            key in item
            for key in [
                "title",
                "content",
                "description",
                "rank",
                "id",
                "index_id",
                "index_name",
                "entity",
                "number of relationships",
                "source",
                "target",
                "weight",
                "links",
            ]
        ):
            st.markdown("---")


def is_valid_list_of_dicts(string):
    try:
        # Attempt to parse the string using ast.literal_eval()
        parsed = ast.literal_eval(string)

        # Check if the result is a list of dictionaries
        if isinstance(parsed, list) and all(isinstance(item, dict) for item in parsed):
            return True
        else:
            return False
    except (ValueError, SyntaxError):
        # If there was an error parsing the string, it's not a valid List[Dict]
        return False
