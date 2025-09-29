"""
Jira connector for fetching ticket information.
"""

import requests
from git_release_helper.connectors.base import BaseConnector

class JiraConnector(BaseConnector):
    """Connector for Jira API."""

    def __init__(self, config):
        """
        Initialize the Jira connector with configuration.

        Args:
            config (dict): Configuration for the Jira connector
        """
        super().__init__(config)
        self.api_url = config.get('api_url', '').rstrip('/')
        self.username = config.get('username', '')
        self.api_key = config.get('api_key', '')
        self.request_timeout = 10

    def _get_auth(self):
        """
        Get the authentication tuple for Jira API requests.

        Returns:
            tuple: Authentication tuple (username, api_key)
        """
        return (self.username, self.api_key)

    def validate_connection(self):
        """
        Validate that the connector can connect to Jira.

        Returns:
            bool: True if connection is valid, False otherwise
        """
        if not self.api_url or not self.username or not self.api_key:
            return False

        try:
            response = requests.get(
                f"{self.api_url}/rest/api/3/myself",
                auth=self._get_auth(),
                timeout=self.request_timeout
            )
            return response.status_code == 200
        except (requests.RequestException, ConnectionError):
            return False

    def get_ticket_details(self, ticket_ids):
        """
        Get details for a list of Jira ticket IDs.

        Args:
            ticket_ids (list): List of Jira ticket IDs to fetch details for

        Returns:
            dict: Mapping of ticket IDs to their details (title, status, etc.)
        """
        if not ticket_ids or not self.validate_connection():
            return {}

        result = {}

        for ticket_id in ticket_ids:
            try:
                response = requests.get(
                    f"{self.api_url}/rest/api/3/issue/{ticket_id}",
                    auth=self._get_auth(),
                    timeout=self.request_timeout
                )

                if response.status_code == 200:
                    issue_data = response.json()
                    result[ticket_id] = {
                        'title': issue_data.get('fields', {}).get('summary', 'Unknown'),
                        'status': issue_data.get('fields', {}).get('status', {}).get(
                            'name', 'Unknown'),
                        'url': f"{self.api_url}/browse/{ticket_id}"
                    }
                else:
                    result[ticket_id] = {
                        'title': 'Could not fetch ticket details',
                        'status': 'Unknown',
                        'url': f"{self.api_url}/browse/{ticket_id}"
                    }
            except (requests.RequestException, ValueError) as exception:
                result[ticket_id] = {
                    'title': f'Error fetching ticket: {str(exception)}',
                    'status': 'Error',
                    'url': f"{self.api_url}/browse/{ticket_id}"
                }

        return result
