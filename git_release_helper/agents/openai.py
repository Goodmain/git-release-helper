"""OpenAI agent for generating summaries of changes."""
import os
import json
import requests
import click

from git_release_helper.agents.base import BaseAgent

class OpenAIAgent(BaseAgent):
    """Agent for OpenAI API to generate summaries."""

    def __init__(self, config):
        """Initialize the OpenAI agent with configuration."""
        super().__init__(config)
        self.api_key = config.get('api_key', os.environ.get('OPENAI_API_KEY', ''))
        self.model = config.get('model', 'gpt-4o')

        if not self.api_key:
            click.echo(
                "Warning: OpenAI API key not provided. "
                "AI summary generation will be skipped."
            )

    def generate_summary(self, commit_messages, max_length=50):
        """Generate a summary of the commit messages using OpenAI API.
        
        Args:
            commit_messages (list): List of commit messages to summarize
            max_length (int): Maximum length of the summary in words
            
        Returns:
            str: Generated summary or None if API call fails
        """
        if not self.api_key:
            return None

        try:
            # Prepare the API request
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }

            # Combine commit messages into a single string
            commits_text = "\n".join(commit_messages)

            # Create the prompt
            prompt = (
                f"Summarize the following ticket titles into a concise release note "
                f"(maximum {max_length} words):\n\n{commits_text}\n\n"
                f"Don't start text with title. Don't use any apostrophe symbols."
            )

            # Prepare the request payload
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 150,  # Approximately 200 characters
                "temperature": 0.5  # More deterministic output
            }

            # Make the API call
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                timeout=30,
                data=json.dumps(payload)
            )

            # Process the response
            if response.status_code == 200:
                result = response.json()

                summary = result["choices"][0]["message"]["content"].strip()

                return summary

            click.echo(f"Error from OpenAI API: {response.status_code} - {response.text}")
            return None

        except (requests.exceptions.RequestException,
                json.JSONDecodeError, KeyError, IndexError) as ex:
            click.echo(f"Error generating summary with OpenAI: {str(ex)}")
            return None
