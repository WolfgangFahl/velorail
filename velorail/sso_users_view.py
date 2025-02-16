"""
Created on 2025-02-15

@author: wf
"""

from fastapi.responses import RedirectResponse
from ngwidgets.login import Login
from ngwidgets.webserver import WebSolution
from nicegui import Client, ui
from wikibot3rd.sso import User
from wikibot3rd.sso_users import Sso_Users


class SsoAuth:
    """
    Encapsulates SSO authentication setup and user handling
    """
    def __init__(self, webserver, debug:bool=False, credentials_path=None):
        """
        Initialize SSO authentication

        Args:
            webserver: The webserver instance to set up SSO for
            debug(bool): if True enable debug mode
            credentials_path: Optional path to the SSO credentials file
        """
        self.users = Sso_Users(webserver.config.short_name, debug=debug, credentials_path=credentials_path)
        self.login = Login(webserver, self.users)

    def get_user(self) -> User:
        """
        Get the current authenticated user

        Returns:
            User: The current user object or None if not authenticated
        """
        user = None
        username = self.login.get_username()
        if username and self.users.is_available:
            user = self.users.sso.get_user(username)
        return user

    def get_user_display_name(self) -> str:
        """
        Get the display name for the current user with admin indicator

        Returns:
            str: Username with optional admin indicator
        """
        username = self.login.get_username()
        if username is None:
            username = "?"
        user = self.get_user()
        admin_flag = "🔑" if user and user.is_admin else ""
        user_display = f"{username}{admin_flag}"
        return user_display

    async def logout(self):
        """Handle user logout"""
        await self.login.logout()

    def as_html(self) -> str:
        """
        Get the user details as HTML markup

        Returns:
            str: HTML markup for the user details or error message
        """
        user = self.get_user()
        html_markup = "<h1>User Details</h1>"
        if not user:
            html_markup += "<p>No user logged in</p>"
        else:
            html_markup += f"""
            <p><strong>ID:</strong> {user.id}</p>
            <p><strong>Name:</strong> {user.name}</p>
            <p><strong>Real Name:</strong> {user.real_name}</p>
            <p><strong>Email:</strong> {user.email}</p>
            <p><strong>Edit Count:</strong> {user.editcount}</p>
            """
        return html_markup


class SsoUsersView:
    """
    View class handling SSO user authentication and user details display
    """
    def __init__(self, solution: WebSolution, sso_auth: SsoAuth):
        """
        Initialize the SSO Users View

        Args:
            solution: The solution instance to handle the view
            sso_auth: The SSO authentication handler
        """
        self.solution = solution
        self.webserver = solution.webserver
        self.auth = sso_auth

    async def show_login(self):
        """Show the login page"""
        await self.auth.login.login(self.solution)

    async def show_user_details(self):
        """Show the user details page"""
        def show():
            self.logout_button = ui.button(
                "logout", icon="logout",
                on_click=self.auth.logout
            )
            ui.html(self.auth.as_html())
        await self.solution.setup_content_div(show)

    def configure_menu(self):
        """Configure the user menu"""
        display_name = self.auth.get_user_display_name()
        self.solution.link_button(display_name, "/user", "person")

    def register_pages(self):
        """Register the SSO-related pages"""
        @ui.page("/user")
        async def show_user(client: Client):
            if not self.auth.login.authenticated():
                return RedirectResponse("/login")
            return await self.webserver.page(
                client, lambda sol: self.show_user_details()
            )

        @ui.page("/login")
        async def login(client: Client):
            return await self.webserver.page(
                client, lambda sol: self.show_login()
            )