# Copyright Jonathan AW.
# Licensed under the MIT License.
import streamlit as st
from src.auth.db import (
    delete_user,
    get_user,
    list_graphrag_indexes,
    list_users,
    save_user,
)
from src.auth.models import User
from src.auth.security import (
    LOCKOUT_THRESHOLD,
    hash_password,
    is_account_locked,
    login_attempts,
    record_failed_attempt,
    reset_failed_attempts,
    verify_password,
)


# Login UI
def login():
    c1, c2 = st.columns([1, 2])
    with c1:
        with st.form("login_form"):
            st.title("User Login")

            username = st.text_input("Username")
            password = st.text_input("Password", type="password")

            if st.form_submit_button("Login"):
                # Init Mode only (To be removed once the CosmoDB is properly initialized with at least 1 Administrator)
                # if (username == "sa" ):
                #     st.success("Login successful")
                #     reset_failed_attempts(username)
                #     st.session_state["username"] = "sa"
                #     st.session_state["permissions"] = "Administrator"
                #     st.experimental_rerun() # Login Success! Halt and reload webpage with new user session!
                user = get_user(username)
                if not user or is_account_locked(username):
                    st.error("Account locked or invalid credentials")
                    return

                if verify_password(user.hashpassword, password):
                    st.success("Login successful")
                    reset_failed_attempts(username)
                    st.session_state["username"] = username
                    st.session_state["permissions"] = user.permissions
                    st.session_state["graphragindexes"] = user.graphragindexes
                    st.experimental_rerun()  # Login Success! Halt and reload webpage with new user session!
                else:
                    record_failed_attempt(username)
                    st.error(
                        f"Invalid credentials. {LOCKOUT_THRESHOLD - login_attempts.get(username, {'count': 0})['count']} attempts left."
                    )


# Logged Out Message
def logout():
    st.session_state.clear()
    st.success(
        "Logged out successfully! Either close the window or click the login button to login again."
    )
    st.button("Login")


def cb_change_password():
    if st.session_state.new_password != st.session_state.confirm_password:
        st.error("Passwords do not match")
        return

    user = get_user(st.session_state["username"])

    if verify_password(user.hashpassword, st.session_state.current_password):
        user.hashpassword = hash_password(st.session_state.new_password, user.salt)
        save_user(user)
        st.session_state.current_password = ""
        st.session_state.new_password = ""
        st.session_state.confirm_password = ""
        st.success("Password changed successfully")
    else:
        st.error("Current password is incorrect")


def change_password():
    if "username" not in st.session_state:
        st.error("You must be logged in to change your password.")
        return

    c1, c2 = st.columns([1, 2])
    with c1:
        with st.form("change_password_form"):
            st.title("Change My Password")

            st.text_input("Current Password", type="password", key="current_password")
            st.text_input("New Password", type="password", key="new_password")
            st.text_input(
                "Confirm New Password", type="password", key="confirm_password"
            )

            if st.form_submit_button("Change Password", on_click=cb_change_password):
                # let the callback handle the rest
                pass


def show_user_details():
    user = get_user(st.session_state.username)
    user.id = "***"
    user.hashpassword = "***"
    user.salt = "***"
    # st.write(f"Username: {user.username}")
    # st.write(f"**Permissions:** {user.permissions}")
    st.dataframe(user, hide_index=True, width=800)
    # st.write(f"**GraphRAG Indexes:** {user.graphragindexes}")


def cb_CreateUser():
    salt_rounds = 12  # Recommended cost factor
    username = st.session_state.create_user_username
    user = User(
        id=username,
        username=username,
        salt=salt_rounds,
        hashpassword=hash_password(st.session_state.create_user_password, salt_rounds),
        permissions=st.session_state.create_user_permissions,
        graphragindexes=st.session_state.create_user_graphragindexes,
        accountstatus="Active",
    )
    save_user(user)
    st.success(f"User {username} created successfully")
    # Clear input fields
    st.session_state.create_user_username = ""
    st.session_state.create_user_password = ""
    st.session_state.create_user_permissions = []
    st.session_state.create_user_graphragindexes = []


def cb_ResetPassword(user):
    salt_rounds = 12  # You can adjust this to increase/decrease the hashing complexity
    user.salt = salt_rounds
    user.hashpassword = hash_password(st.session_state.reset_password, user.salt)
    save_user(user)
    st.success(f"Password for {user.username} has been reset successfully")
    st.session_state.reset_password = ""
    st.session_state.confirm_reset_password = ""


def cb_DeleteUser():
    if st.session_state.confirm_delete:
        username = st.session_state.delete_user_username
        if delete_user(username):
            st.success(f"User {username} deleted successfully.")
        else:
            st.error(f"Failed to delete user {username}.")
    else:
        st.warning("Please confirm the deletion by checking the box.")


def cb_unlock_account(user):
    user.accountstatus = "Active"
    save_user(user)
    st.success(f"User {user.username} unlocked successfully")


def admin_interface():
    check_permission("Administrator")  # assert permission

    c1, c2 = st.columns([1, 2])
    with c1:
        st.title("User Administration")
        action = st.selectbox(
            "Select Action",
            [
                "Create User",
                "Edit User",
                "Unlock Account",
                "Reset Password",
                "Delete User",
            ],
        )

        users = list_users()
        user_options = [user["username"] for user in users]
        graphrag_indexes = list_graphrag_indexes()  # Get available indexes

        if action == "Create User":
            with st.form("create_user_form"):
                st.text_input("Username", key="create_user_username")
                st.text_input(
                    "Default Password", type="password", key="create_user_password"
                )
                permissions = st.multiselect(
                    "Permissions",
                    ["Administrator", "AllowCreateIndex", "AllowQuery"],
                    key="create_user_permissions",
                )
                selected_indexes = st.multiselect(
                    "GraphRAG Indexes",
                    graphrag_indexes,
                    key="create_user_graphragindexes",
                )

                if st.form_submit_button("Create User", on_click=cb_CreateUser):
                    # Let Callback handle the rest
                    pass

        elif action == "Edit User":
            selected_username = st.selectbox("Select User to Edit", user_options)
            user = get_user(selected_username)

            if user:
                with st.form("edit_user_form"):
                    permissions = st.multiselect(
                        "Permissions",
                        ["Administrator", "AllowCreateIndex", "AllowQuery"],
                        default=user.permissions,
                    )
                    selected_indexes = st.multiselect(
                        "GraphRAG Indexes",
                        graphrag_indexes,
                        default=user.graphragindexes,
                    )

                    if st.form_submit_button("Update User"):
                        user.permissions = permissions
                        user.graphragindexes = selected_indexes
                        save_user(user)
                        st.success(f"User {selected_username} updated successfully")

            else:
                st.error("User not found")

        elif action == "Unlock Account":
            selected_username = st.selectbox("Select User to Unlock", user_options)
            user = get_user(selected_username)

            if user:
                f"Status: {user.accountstatus}"
                if user.accountstatus == "Active":
                    st.info("Account is already active!")
                elif st.button(
                    "Unlock Account", on_click=cb_unlock_account, args=[user]
                ):
                    # Let Callback handle the rest
                    pass
            else:
                st.error("User not found")

        elif action == "Reset Password":
            selected_username = st.selectbox(
                "Select User to Reset Password", user_options
            )
            user = get_user(selected_username)

            if user:
                with st.form("reset_password_form"):
                    new_password = st.text_input(
                        "New Password", type="password", key="reset_password"
                    )
                    confirm_password = st.text_input(
                        "Confirm New Password",
                        type="password",
                        key="confirm_reset_password",
                    )

                    if new_password != confirm_password:
                        st.error("Passwords do not match")
                    else:
                        if st.form_submit_button(
                            "Reset Password", on_click=cb_ResetPassword, args=[user]
                        ):
                            # Let Callback handle the rest
                            pass
            else:
                st.error("User not found")

        elif action == "Delete User":
            selected_username = st.selectbox(
                "Select User to Delete", user_options, key="delete_user_username"
            )
            user = get_user(selected_username)

            if user:
                # Prevent the administrator from deleting their own account
                if selected_username == st.session_state["username"]:
                    st.warning("You cannot delete your own account.")
                else:
                    st.checkbox("Confirm delete user?", key="confirm_delete")
                    if st.button("Delete User", on_click=cb_DeleteUser):
                        # Let Callback handle the rest
                        pass
            else:
                st.error("User not found")


def check_permission(required_permission):
    if (
        "permissions" not in st.session_state
        or required_permission not in st.session_state["permissions"]
    ):
        st.error("You do not have permission to access this section.")
        st.stop()


if __name__ == "__main__":
    st.set_page_config(layout="wide")
    st.title("MOH AIM - GraphRAG Copilot")
    loginPage = st.Page(login, title="User Login")
    UsersAdminPage = st.Page(admin_interface, title="Users Administration")
    mainPage = st.Page("app.py", title="MOH ACE GraphRAG Copilot")
    show_user_detailsPage = st.Page(show_user_details, title="User Details")
    changePasswordPage = st.Page(change_password, title="Change Password")
    logoutPage = st.Page(logout, title="Logout")

    if "username" not in st.session_state:
        pg = st.navigation([loginPage])
    elif (
        "permissions" in st.session_state
        and "Administrator" in st.session_state["permissions"]
    ):
        st.write(f"Welcome {st.session_state['username']}")
        pg = st.navigation(
            {
                "Copilot": [mainPage],
                "Administrator": [UsersAdminPage],
                "Account": [show_user_detailsPage, changePasswordPage, logoutPage],
            }
        )
    else:
        st.write(f"Welcome {st.session_state['username']}")
        pg = st.navigation(
            {
                "Copilot": [mainPage],
                "Account": [show_user_detailsPage, changePasswordPage, logoutPage],
            }
        )
    pg.run()
