import click
import git
import os
import re
import datetime
import yaml
from git_release_helper.config import (
    get_default_branches, get_config_path, get_ticket_pattern, get_tag_format,
    get_project_name, get_message_format, get_templates_dir, ensure_templates_dir,
    get_connector_type, get_connector_config
)
from git_release_helper.connectors import get_connector


def get_repo():
    """Get the current git repository."""
    try:
        return git.Repo(os.getcwd())
    except git.exc.InvalidGitRepositoryError:
        click.echo("Current directory is not a git repository.")
        return None


def validate_branch(repo, force=False):
    """Validate if current branch is a default branch."""
    current_branch = repo.active_branch.name
    default_branches = get_default_branches()
    
    if current_branch not in default_branches and not force:
        click.echo(f"Warning: You are not on a default branch. Current branch: {current_branch}")
        click.echo(f"Default branches: {', '.join(default_branches)}")
        return click.confirm("Do you want to proceed anyway?")
    return True


def generate_tag_name(repo):
    """Generate a new tag name based on the configured format."""
    # Get the tag format from config
    tag_format = get_tag_format()
    today = datetime.datetime.now()
    
    # Replace placeholders in the tag format
    tag_base = tag_format
    tag_base = tag_base.replace("YYYY", today.strftime("%Y"))
    tag_base = tag_base.replace("YY", today.strftime("%y"))
    tag_base = tag_base.replace("MM", today.strftime("%m"))
    tag_base = tag_base.replace("DD", today.strftime("%d"))
    
    # Create a regex pattern to match existing tags with the same format
    tag_pattern = tag_base.replace("N", r"(\d+)")
    tag_regex = re.compile(tag_pattern)
    
    # Find all tags matching today's format
    matching_tags = []
    for t in repo.tags:
        match = tag_regex.match(t.name)
        if match:
            try:
                n = int(match.group(1))
                matching_tags.append((t.name, n))
            except (ValueError, IndexError):
                continue
    
    # Determine the next sequence number
    next_n = 1
    if matching_tags:
        next_n = max([n for _, n in matching_tags]) + 1
    
    # Set the new tag name
    return tag_base.replace("N", str(next_n))


def find_last_tag(repo):
    """Find the most recently created tag in the repository."""
    try:
        # Sort tags by commit date in descending order
        tags = sorted(repo.tags, key=lambda t: t.commit.committed_datetime, reverse=True)
        if tags:
            return tags[0].name
        return None
    except Exception as e:
        click.echo(f"Error finding last tag: {str(e)}")
        return None


def extract_tickets_from_commits(commits, ticket_pattern):
    """Extract ticket numbers from commit messages."""
    ticket_regex = re.compile(ticket_pattern)
    tickets = set()
    
    for commit in commits:
        commit_message = commit.message.strip()
        matches = ticket_regex.findall(commit_message)
        tickets.update(matches)
    
    return sorted(tickets)


def generate_release_message(project_name, tag, tickets, format_to_use, ticket_details=None):
    """Generate a release message based on the specified format."""
    template_file = os.path.join(get_templates_dir(), f"{format_to_use}.template")
    
    # Read template file
    try:
        with open(template_file, 'r') as f:
            template_content = f.read()
    except:
        # Fallback to default template if file can't be read
        if format_to_use == 'markdown':
            template_content = "# Deploying [PROJECT_NAME] `[TAG_NAME]`\n\n## Tickets:\n[TICKETS_LIST]"
        else:
            template_content = "Deploying [PROJECT_NAME] [TAG_NAME]\n\nTickets:\n[TICKETS_LIST]"
    
    # Format tickets list based on format
    if tickets:
        if ticket_details:
            # Include ticket titles and statuses if available
            tickets_list = []
            for ticket in tickets:
                ticket_info = ticket_details.get(ticket, {})
                title = ticket_info.get('title', '')
                status = ticket_info.get('status', '')
                
                if title and status:
                    tickets_list.append(f"- {ticket}: {title} ({status})")
                elif title:
                    tickets_list.append(f"- {ticket}: {title}")
                else:
                    tickets_list.append(f"- {ticket}")
            
            tickets_list = "\n".join(tickets_list)
        else:
            tickets_list = "\n".join([f"- {ticket}" for ticket in tickets])
    else:
        tickets_list = "No tickets found in this release."
    
    # Replace placeholders in template
    release_message = template_content
    release_message = release_message.replace("[PROJECT_NAME]", project_name)
    release_message = release_message.replace("[TAG_NAME]", tag)
    release_message = release_message.replace("[TICKETS_LIST]", tickets_list)
    
    return release_message


def check_remote_branch(repo, current_branch):
    """Check if local branch is outdated compared to remote."""
    remote_refs = {}
    for remote in repo.remotes:
        try:
            for ref in remote.refs:
                remote_refs[ref.name.split('/')[-1]] = ref
        except AssertionError:
            # Remote has no references
            continue
    
    if current_branch in remote_refs:
        remote_branch = remote_refs[current_branch]
        local_commit_count = len(list(repo.iter_commits(f"{remote_branch.name}..{current_branch}")))
        behind_count = len(list(repo.iter_commits(f"{current_branch}..{remote_branch.name}")))
        
        if behind_count > 0:
            click.echo(f"\nYour local branch is {behind_count} commit{'s' if behind_count > 1 else ''} behind the remote.")
            click.echo("Updating your branch is recommended to ensure you have the latest changes.")
            if click.confirm("Would you like to update your local branch now?"):
                click.echo("Pulling latest changes...")
                repo.remotes.origin.pull()
                click.echo("Branch updated successfully.")
            else:
                click.echo("Continuing with local branch state.")


def get_project_name(repo):
    """Extract project name from repository."""
    try:
        # First check if project_name is set in config
        from git_release_helper.config import get_project_name as get_configured_project_name
        configured_name = get_configured_project_name()
        if configured_name:
            return configured_name
            
        # Otherwise extract from git repo
        if hasattr(repo, 'remotes') and repo.remotes:
            # Try to extract from remote URL
            remote_url = repo.remotes.origin.url
            if remote_url:
                # Extract project name from remote URL
                # Handle different formats: https://github.com/user/project.git or git@github.com:user/project.git
                if remote_url.endswith('.git'):
                    remote_url = remote_url[:-4]  # Remove .git suffix
                
                project_name = os.path.basename(remote_url)
                if project_name:
                    return project_name
                
        # Fallback to directory name
        dir_name = os.path.basename(os.path.normpath(repo.working_dir))
        if dir_name:
            return dir_name
            
        return "Unknown Project"
    except Exception as e:
        print(f"Error getting project name: {str(e)}")
        return "Unknown Project"


def handle_tag(repo, tag):
    """Handle tag validation or generation and return tag information."""
    tag_exists = False
    if not tag:
        tag = generate_tag_name(repo)
        project_name = get_project_name(repo)
        click.echo(f"Generated tag name for {project_name}: {tag}")
    else:
        # Check if the provided tag exists
        try:
            repo.tags[tag]
            tag_exists = True
            click.echo(f"Error: Tag '{tag}' already exists in the repository.")
            click.echo("Please specify a different tag name or let the application generate one.")
            return None, None
        except IndexError:
            click.echo(f"Tag '{tag}' will be created at the end of the process with your confirmation.")
    
    return tag, tag_exists


def prepare_release(repo, tag, tag_exists, message_format):
    """Prepare release information including commits, tickets, and message."""
    # Find the last tag in the repository
    last_tag = None
    if not tag_exists:
        last_tag = find_last_tag(repo)
    else:
        last_tag = tag
    
    # Get commits after the last tag
    commits_after_tag = []
    if last_tag:
        try:
            commits_after_tag = list(repo.iter_commits(f"{last_tag}..HEAD"))
            
            # Display information about the last tag
            tag_commit = repo.tags[last_tag].commit
            tag_commit_message = tag_commit.message.strip()
            
            click.echo(f"\nPreparing release based on changes after tag: {last_tag}")
            click.echo(f"Last tag commit: {tag_commit.hexsha}")
            click.echo(f"Last tag message: {tag_commit_message}")
            
            # Check if there are any commits after the tag
            if not commits_after_tag:
                click.echo(f"Error: No commits found after tag '{last_tag}'.")
                click.echo("There's nothing to release. Create new commits before making a release.")
                return None
        except (IndexError, git.exc.GitCommandError) as e:
            click.echo(f"Error analyzing commits after tag: {str(e)}")
            return None
    else:
        # No tags exist, use all commits
        commits_after_tag = list(repo.iter_commits())
        click.echo("\nNo previous tags found. Using all commits for this release.")
    
    # Extract ticket names from commit messages
    ticket_pattern = get_ticket_pattern()
    tickets = extract_tickets_from_commits(commits_after_tag, ticket_pattern)
    
    # Get ticket details from connector if available
    ticket_details = {}
    connector_type = get_connector_type()
    if connector_type and tickets:
        click.echo(f"\nFetching ticket details from {connector_type.upper()}...")
        try:
            connector_config = get_connector_config(connector_type)
            connector = get_connector(connector_type, connector_config)
            
            if connector and connector.validate_connection():
                ticket_details = connector.get_ticket_details(tickets)
                if ticket_details:
                    click.echo("Successfully retrieved ticket details.")
                else:
                    click.echo("No ticket details could be retrieved.")
            else:
                click.echo(f"Could not connect to {connector_type.upper()}. Check your configuration.")
        except Exception as e:
            click.echo(f"Error connecting to {connector_type.upper()}: {str(e)}")
    
    # Display ticket information
    if tickets:
        click.echo("\nHere is the list of tickets that were merged after last release:")
        for ticket in tickets:
            ticket_title = ticket_details.get(ticket, {}).get('title', '')
            ticket_status = ticket_details.get(ticket, {}).get('status', '')
            if ticket_title:
                if ticket_status:
                    click.echo(f"- {ticket}: {ticket_title} ({ticket_status})")
                else:
                    click.echo(f"- {ticket}: {ticket_title}")
            else:
                click.echo(f"- {ticket}")
    else:
        click.echo("\nNo tickets found in commits after the last release.")
    
    # Get project name from repository
    project_name = get_project_name(repo)
    
    # Determine message format to use
    format_to_use = message_format if message_format else get_message_format()
    
    # Generate release message
    release_message = generate_release_message(project_name, tag, tickets, format_to_use, ticket_details)
    
    return release_message


@click.group()
def main():
    """Git Release Helper CLI."""
    pass


@main.command()
@click.option('--tag', help='The tag to create a release from. If not provided, a new tag will be generated.')
@click.option('--force', '-f', is_flag=True, help='Skip branch validation and confirmation.')
@click.option('--show-config', is_flag=True, help='Show the path to the configuration file and exit.')
@click.option('--format', 'message_format', type=click.Choice(['markdown', 'plain']), 
              help='Format for the release message. Overrides the configuration setting.')
def release(tag, force, show_config, message_format):
    """Create a new release."""
    try:
        # Ensure templates directory exists
        ensure_templates_dir()
        
        # Show configuration file path and contents if requested
        if show_config:
            from git_release_helper.config import get_config_path, get_local_config_path, get_config_content, load_config
            
            # Show global configuration
            global_config_path = get_config_path()
            click.echo(f"Global configuration file: {global_config_path}")
            click.echo("=====================")
            if os.path.exists(global_config_path):
                click.echo(get_config_content(global_config_path))
            else:
                click.echo("Global configuration file does not exist.")
            click.echo()
            
            # Show local configuration if it exists
            local_config_path = get_local_config_path()
            if local_config_path:
                click.echo(f"Local configuration file: {local_config_path}")
                click.echo("=====================")
                click.echo(get_config_content(local_config_path))
                click.echo()
                
                click.echo("Final configuration:")
                click.echo("=====================")
                click.echo(yaml.dump(load_config(), default_flow_style=False, sort_keys=False))
            
            return
            
        # Get the current repository
        repo = get_repo()
        if not repo:
            return
        
        # Validate current branch
        if not validate_branch(repo, force):
            click.echo("Operation cancelled.")
            return
        
        # Handle tag (generate or validate)
        tag, tag_exists = handle_tag(repo, tag)
        if tag is None:
            return
        
        # Check if local branch is outdated
        current_branch = repo.active_branch.name
        check_remote_branch(repo, current_branch)
        
        # Prepare release information
        release_message = prepare_release(repo, tag, tag_exists, message_format)
        if release_message is None:
            return
        
        # Display the release message
        click.echo("\nGenerated Release Message:")
        click.echo("==========================")
        click.echo(release_message)
        click.echo("==========================")
        
        # Ask for confirmation to create the tag
        if not tag_exists:
            if click.confirm(f"\nDo you want to create the tag '{tag}' now?"):
                click.echo(f"Creating new tag: {tag}")
                new_tag = repo.create_tag(tag, message=f"Release {tag}")
                click.echo(f"Tag {tag} created successfully")
            else:
                click.echo("Tag creation cancelled.")
                return
        
        click.echo("\nTo create a GitHub release, use the following information:")
        click.echo(f"Tag: {tag}")
        click.echo(f"Title: Release {tag}")
        click.echo(f"Description: Use the generated release message above")
        
    except git.exc.InvalidGitRepositoryError:
        click.echo("Current directory is not a git repository.")
    except Exception as e:
        click.echo(f"An error occurred: {str(e)}")


@main.command()
def init():
    """Initialize local project configuration."""
    from git_release_helper.config import generate_local_config
    
    try:
        # Get the repository to verify we're in a git repo
        repo = get_repo()
        if not repo:
            click.echo("Cannot initialize configuration: Not a git repository.")
            return
        
        # Generate local config file
        if generate_local_config():
            click.echo("Local configuration initialized successfully.")
            click.echo("You can now edit .release_config.yml to customize settings for this project.")
        else:
            click.echo("Failed to initialize local configuration.")
    
    except Exception as e:
        click.echo(f"An error occurred: {str(e)}")


if __name__ == '__main__':
    main()