import os
import yaml
import click

# Default configuration values
DEFAULT_CONFIG = {
    "default_branches": ["main", "master"],
    "commit_message_format": "TICKET_NAME: Commit message",
    "ticket_pattern": "ALLI-[0-9]+",
    "tag_format": "YYYYMMDD.N",
    "project_aliases": {},
    "message_format": "markdown",
    "templates_dir": "./templates"
}

# Configuration paths
CONFIG_DIR = os.path.expanduser("~/.git-release-helper")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.yml")

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
        with open(markdown_template_path, "w") as f:
            f.write("# Deploying [PROJECT_NAME] `[TAG_NAME]`\n\n")
            f.write("## Tickets:\n")
            f.write("[TICKETS_LIST]")
    
    # Create default plain text template
    plain_template_path = os.path.join(templates_dir, "plain.template")
    if not os.path.exists(plain_template_path):
        with open(plain_template_path, "w") as f:
            f.write("Deploying [PROJECT_NAME] [TAG_NAME]\n\n")
            f.write("Tickets:\n")
            f.write("[TICKETS_LIST]")

def load_config():
    """Load configuration from file or create default if it doesn't exist."""
    ensure_config_dir()
    
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return yaml.safe_load(f) or DEFAULT_CONFIG
        except (yaml.YAMLError, IOError) as e:
            click.echo(f"Error loading config file: {str(e)}")
            click.echo("Using default configuration.")
            return DEFAULT_CONFIG
    
    # No config found, create default
    save_config(DEFAULT_CONFIG)
    return DEFAULT_CONFIG

def save_config(config):
    """Save configuration to YAML file."""
    ensure_config_dir()
    
    try:
        with open(CONFIG_FILE, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    except IOError as e:
        click.echo(f"Error saving config file: {str(e)}")

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

def get_project_aliases():
    """Get the project aliases dictionary."""
    config = load_config()
    return config.get("project_aliases", DEFAULT_CONFIG["project_aliases"])

def get_message_format():
    """Get the message format (markdown or plain)."""
    config = load_config()
    return config.get("message_format", DEFAULT_CONFIG["message_format"])

def get_templates_dir():
    """Get the templates directory path."""
    config = load_config()
    templates_dir = config.get("templates_dir", DEFAULT_CONFIG["templates_dir"])
    return os.path.expanduser(templates_dir)

def set_default_branches(branches):
    """Set the list of default branch names."""
    config = load_config()
    config["default_branches"] = branches
    save_config(config)

def get_config_path():
    """Get the path to the configuration file."""
    return CONFIG_FILE