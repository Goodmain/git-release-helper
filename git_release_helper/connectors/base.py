"""
Base connector interface for ticket management systems.
"""

from abc import ABC, abstractmethod

class BaseConnector(ABC):
    """Base class for all ticket system connectors."""

    def __init__(self, config):
        """
        Initialize the connector with configuration.

        Args:
            config (dict): Configuration for the connector
        """
        self.config = config

    @abstractmethod
    def get_ticket_details(self, ticket_ids):
        """
        Get details for a list of ticket IDs.

        Args:
            ticket_ids (list): List of ticket IDs to fetch details for

        Returns:
            dict: Mapping of ticket IDs to their details (title, status, etc.)
        """

    @abstractmethod
    def validate_connection(self):
        """
        Validate that the connector can connect to the ticket system.

        Returns:
            bool: True if connection is valid, False otherwise
        """
