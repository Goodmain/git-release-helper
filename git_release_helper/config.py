import os
import yaml
import click
import git

# Default configuration values
DEFAULT_CONFIG = {
    "default_branches": ["main", "master"],
    "commit_message_format": "TICKET_NAME: Commit message",
    "ticket_pattern": "ALLI-[0-9]+",
    "tag_format": "YYYYMMDD.N",
    "project_name": None,
    "message_format": "markdown",
    "templates_dir": "./templates",
    "connectors": {
        "type": None,  # Options: None, "jira", "github", "gitlab", etc.
        "jira": {
            "api_url": "https://your-jira-instance.atlassian.net",
            "api_key": "",
            "username": ""
        }
    }
}

# Configuration paths
CONFIG_DIR = os.path.expanduser("~/.git-release-helper")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.yml")
LOCAL_CONFIG_FILE = ".release_config.yml"

# Global configuration variable
_CONFIG = None

def ensure_config_dir():
    """Ensure the config directory exists."""
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)

def ensure_templates_dir():
    """Ensure the templates directory exists and has default templates."""
    templates_dir = get_templates_dir()
    if not os.path.exists(templates_dir):
        os.makedirs(templates_dir)

    # Create default markdown template
    markdown_template_path = os.path.join(templates_dir, "markdown.template")
    if not os.path.exists(markdown_template_path):
        with open(markdown_template_path, "w", encoding="utf-8") as file:
            file.write("# Deploying [PROJECT_NAME] `[TAG_NAME]`\n\n")
            file.write("## Tickets:\n")
            file.write("[TICKETS_LIST]")

    # Create default plain text template
    plain_template_path = os.path.join(templates_dir, "plain.template")
    if not os.path.exists(plain_template_path):
        with open(plain_template_path, "w", encoding="utf-8") as file:
            file.write("Deploying [PROJECT_NAME] [TAG_NAME]\n\n")
            file.write("Tickets:\n")
            file.write("[TICKETS_LIST]")

def load_config():
    """Load configuration from file or create default if it doesn't exist."""
    global _CONFIG

    # Return already loaded config if available
    if _CONFIG is not None:
        return _CONFIG

    ensure_config_dir()

    # Start with default config
    config = DEFAULT_CONFIG.copy()

    # Load global config if exists
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as file:
                global_config = yaml.safe_load(file)
                if global_config:
                    config.update(global_config)
        except (yaml.YAMLError, IOError) as exception:
            click.echo(f"Error loading global config file: {str(exception)}")

    # Load local config if exists (overrides global config)
    if os.path.exists(LOCAL_CONFIG_FILE):
        try:
            with open(LOCAL_CONFIG_FILE, 'r', encoding='utf-8') as file:
                local_config = yaml.safe_load(file)
                if local_config:
                    # Merge connectors section if it exists in both configs
                    if 'connectors' in local_config and 'connectors' in config:
                        if local_config['connectors'].get('type'):
                            config['connectors']['type'] = local_config['connectors']['type']

                        # Merge connector-specific configs
                        for connector_name, connector_config in local_config['connectors'].items():
                            if connector_name != 'type' and connector_name in config['connectors']:
                                config['connectors'][connector_name].update(connector_config)

                    # Update other top-level keys
                    for key, value in local_config.items():
                        if key != 'connectors':
                            config[key] = value

                    click.echo("Local config loaded and applied.")
        except (yaml.YAMLError, IOError) as exception:
            click.echo(f"Error loading local config file: {str(exception)}")

    # Store in global variable
    _CONFIG = config

    return config

def save_config(config):
    """Save configuration to YAML file."""
    ensure_config_dir()

    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as file:
            yaml.dump(config, file, default_flow_style=False, sort_keys=False)
    except IOError as exception:
        click.echo(f"Error saving config file: {str(exception)}")

def get_default_branches():
    """Get the list of default branch names."""
    config = load_config()
    return config.get("default_branches", DEFAULT_CONFIG["default_branches"])

def get_commit_message_format():
    """Get the commit message format."""
    config = load_config()
    return config.get("commit_message_format", DEFAULT_CONFIG["commit_message_format"])

def get_ticket_pattern():
    """Get the ticket pattern regex."""
    config = load_config()
    return config.get("ticket_pattern", DEFAULT_CONFIG["ticket_pattern"])

def get_tag_format():
    """Get the tag format pattern."""
    config = load_config()
    return config.get("tag_format", DEFAULT_CONFIG["tag_format"])

def get_project_name():
    """Get the project name."""
    config = load_config()
    return config.get("project_name", DEFAULT_CONFIG["project_name"])

def get_message_format():
    """Get the message format (markdown or plain)."""
    config = load_config()
    return config.get("message_format", DEFAULT_CONFIG["message_format"])

def get_templates_dir():
    """Get the templates directory path."""
    config = load_config()
    templates_dir = config.get("templates_dir", DEFAULT_CONFIG["templates_dir"])
    return os.path.expanduser(templates_dir)

def get_project_name_from_git():
    """Get project name from git remote URL."""
    try:
        repo = git.Repo(os.getcwd())
        if not repo.remotes:
            return None

        # Try to extract project name from the first remote URL
        remote_url = repo.remotes[0].url

        # Extract project name from remote URL
        # Handle different formats: https://github.com/user/project.git
        # or git@github.com:user/project.git
        if remote_url.endswith('.git'):
            remote_url = remote_url[:-4]  # Remove .git suffix

        project_name = os.path.basename(remote_url)
        return project_name
    except (git.InvalidGitRepositoryError, git.NoSuchPathError, IndexError):
        return None

def generate_local_config():
    """Generate a local config file with project-specific settings."""
    # Try to get project name from git
    project_name = get_project_name_from_git()

    if not project_name:
        click.echo("Could not determine project name from git. Local config not created.")
        return False

    # Create minimal local config with project name and connector set to None
    local_config = {
        "project_name": project_name,
        "connectors": {
            "type": None
        }
    }

    # Save local config
    try:
        with open(LOCAL_CONFIG_FILE, 'w', encoding="utf-8") as file:
            yaml.dump(local_config, file, default_flow_style=False, sort_keys=False)
        click.echo(f"Local config file created: {LOCAL_CONFIG_FILE}")
        return True
    except IOError as exception:
        click.echo(f"Error creating local config file: {str(exception)}")
        return False

def set_default_branches(branches):
    """Set the list of default branch names."""
    config = load_config()
    config["default_branches"] = branches
    save_config(config)

def get_config_path():
    """Get the path to the configuration file."""
    return CONFIG_FILE

def get_local_config_path():
    """Get the path to the local configuration file if it exists."""
    if os.path.exists(LOCAL_CONFIG_FILE):
        return os.path.abspath(LOCAL_CONFIG_FILE)
    return None

def get_config_content(config_path):
    """Get the content of a configuration file as a formatted string."""
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            config_content = yaml.safe_load(file)
            return yaml.dump(config_content, default_flow_style=False, sort_keys=False)
    except (yaml.YAMLError, IOError) as exception:
        return f"Error reading config file: {str(exception)}"

def get_connector_type():
    """Get the configured connector type."""
    config = load_config()
    return config.get("connectors", {}).get("type")

def get_connector_config(connector_type):
    """Get the configuration for a specific connector."""
    config = load_config()
    return config.get("connectors", {}).get(connector_type, {})
