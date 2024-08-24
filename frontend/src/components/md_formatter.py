import ast

import streamlit as st


def display_markdown_text(text: str):
    """
    Display markdown text.

    This function will be able to perform special handling if the text is a Python Dictionary

    Parameters:
    text (str): The markdown text to be displayed.

    Returns:
    None
    """
    try:
        # Attempt to parse the string using ast.literal_eval()
        parsed = ast.literal_eval(text)

        # Check if the result is a list of dictionaries
        if isinstance(parsed, list) and all(isinstance(item, dict) for item in parsed):
            display_pythonListDict_as_markdown(parsed)
        else:
            st.markdown(escape_special_chars(text))
    except (ValueError, SyntaxError):
        # If there was an error parsing the string, it's not a valid List[Dict]
        st.markdown(escape_special_chars(text))


def display_pythonListDict_as_markdown(listDict):
    for item in listDict:
        # Process common fields that might exist in all dictionary types
        if "title" in item:
            st.markdown(f"### {escape_special_chars(item['title'])}")

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
            st.markdown(escape_special_chars(item["content"]))

        if "description" in item:
            st.markdown(escape_special_chars(item["description"]))

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


def escape_special_chars(text: str, chars_to_escape=["$"]) -> str:
    """
    Escapes special characters in the text for proper Markdown rendering in Streamlit.

    Args:
        text (str): The input text to be processed.
        chars_to_escape (list, optional): A list of characters to escape. Defaults to ['$'].

    Returns:
        str: The processed text with special characters escaped.
    """
    if chars_to_escape is None:
        chars_to_escape = ["$"]

    for char in chars_to_escape:
        text = text.replace(char, f"\\{char}")

    return text
