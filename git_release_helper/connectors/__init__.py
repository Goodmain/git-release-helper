"""
Connectors for integrating with various ticket management systems.
"""

from git_release_helper.connectors.base import BaseConnector
from git_release_helper.connectors.jira import JiraConnector

def get_connector(connector_type, config):
    """
    Factory function to get the appropriate connector based on type.

    Args:
        connector_type (str): The type of connector to use (e.g., 'jira')
        config (dict): Configuration for the connector

    Returns:
        BaseConnector: An instance of the appropriate connector
    """
    if not connector_type:
        return None

    if connector_type.lower() == 'jira':
        return JiraConnector(config)

    return None
