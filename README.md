# Git Release Helper

A command-line tool to help create releases from git tags with support for ticket tracking and CRM integration.

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/py-git-release-helper.git
cd py-git-release-helper

# Install the package
pip install -e .
```

## Usage

The tool provides several commands to help with release management:

```bash
# Create a new release
git-release-helper release

# Use a specific tag
git-release-helper release --tag v1.0.0

# Skip branch validation
git-release-helper release --force

# Initialize local project configuration
git-release-helper init
```

## Features

- Automatically generates tag names based on configurable formats
- Extracts ticket references from commit messages
- Fetches ticket details from CRM systems (Jira support included)
- Creates release notes with ticket information
- Supports both global and project-specific configurations

## Configuration

### Global Configuration

The tool stores global configuration in `~/.git-release-helper/config.yml`. The default configuration is created automatically on first run.

```bash
# Show configuration details
git-release-helper release --show-config
```

The `--show-config` option displays:
- Global configuration file path and contents
- Local configuration file path and contents (if present)
- Final configuration (when local config exists)

### Local Project Configuration

You can create a project-specific configuration that overrides global settings:

```bash
# Initialize local configuration
git-release-helper init
```

This creates a `.release_config.yml` file in your project directory with project-specific settings.

### Default Branches

By default, the tool checks if you're on a default branch (`main` or `master`) before proceeding. You can modify the list of default branches by editing the configuration file:

```yaml
default_branches:
  - main
  - master
  - develop
```

### Commit Message Format

The tool extracts ticket names from commit messages based on a configured pattern. You can customize the expected format:

```yaml
# Format used for commit messages
commit_message_format: "TICKET_NAME: Commit message"
```

### Ticket Pattern

The regular expression pattern used to identify ticket names in commit messages:

```yaml
# Regex pattern for ticket names (default: ALLI-123)
ticket_pattern: "ALLI-[0-9]+"
```

### Tag Format

The format used for automatically generated tags when no tag is specified:

```yaml
# Format for auto-generated tags
tag_format: "YYYYMMDD.N"
```

Supported placeholders:
- `YYYY`: 4-digit year (e.g., 2023)
- `YY`: 2-digit year (e.g., 23)
- `MM`: 2-digit month (e.g., 01)
- `DD`: 2-digit day (e.g., 05)
- `N`: Incremental number for multiple tags on the same day

Examples:
- `YYYY-MM-DD.N` → `2023-01-05.1`
- `release-YY.MM.N` → `release-23.01.1`
- `my-tag-MMDD.N` → `my-tag-0105.1`

### CRM Connectors

The tool can integrate with CRM systems to fetch ticket details. Currently supported:

#### Jira

```yaml
connectors:
  type: "jira"
  jira:
    api_url: "https://your-jira-instance.atlassian.net"
    api_key: "your-api-key"
    username: "your-email@example.com"
```

### Message Format

You can customize the format of release messages:

```yaml
# Format for release messages (markdown or plain)
message_format: "markdown"
```

Custom templates can be added to the templates directory.

### Message Format

Choose the format for release messages:

```yaml
# Format for release messages (markdown or plain)
message_format: "markdown"
```

### Message Templates

The tool uses templates to generate release messages. Templates are stored in the `templates` directory:

```yaml
# Location of message templates
templates_dir: "./templates"
```

Default templates are provided for both markdown and plain text formats. You can customize these templates by editing the files in the templates directory.

Templates support the following placeholders:
- `[PROJECT_NAME]`: The repository name or its alias if defined
- `[TAG_NAME]`: The tag name for the release
- `[TICKETS_LIST]`: The formatted list of tickets included in the release

### Configuration Template

A template configuration file is provided at `config.yml.template` that you can use as a reference.

## Features

- Automatically uses the latest tag if no tag is specified
- Provides formatted information for creating a GitHub release
- Shows the commit message associated with the tag
- Validates current branch against configured default branches
- Configurable default branch names
- Extracts and displays unique ticket names from commits since the last release
- Configurable ticket name pattern matching
- Automatic tag creation with configurable format
- Project name extraction from repository or configuration
- Configurable project name
- Release message generation in markdown or plain text format
- Customizable message templates

## Requirements

- Python 3.6+
- Git repository
- GitPython
- Click

## License

MIT