import click
import git
import os
import re
import datetime
from git_release_helper.config import (
    get_default_branches, get_config_path, get_ticket_pattern, get_tag_format,
    get_project_aliases, get_message_format, get_templates_dir, ensure_templates_dir
)

@click.command()
@click.option('--tag', help='The tag to create a release from. If not provided, the latest tag will be used.')
@click.option('--force', '-f', is_flag=True, help='Skip branch validation and confirmation.')
@click.option('--show-config', is_flag=True, help='Show the path to the configuration file and exit.')
@click.option('--format', 'message_format', type=click.Choice(['markdown', 'plain']), 
              help='Format for the release message. Overrides the configuration setting.')
def main(tag, force, show_config, message_format):
    """GitHub Release Helper - A tool for creating GitHub releases."""
    # Ensure templates directory exists
    ensure_templates_dir()
    
    # Show configuration file path if requested
    if show_config:
        config_path = get_config_path()
        click.echo(f"Configuration file: {config_path}")
        return
        
    try:
        # Get the current repository
        repo_path = os.getcwd()
        repo = git.Repo(repo_path)
        
        # Check if current branch is a default branch
        current_branch = repo.active_branch.name
        default_branches = get_default_branches()
        
        if current_branch not in default_branches and not force:
            click.echo(f"Warning: You are not on a default branch. Current branch: {current_branch}")
            click.echo(f"Default branches: {', '.join(default_branches)}")
            if not click.confirm("Do you want to proceed anyway?"):
                click.echo("Operation cancelled.")
                return
        
        # If tag is not provided, create a new tag based on the configured format
        if not tag:
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
            # Replace N with a regex pattern to capture the number
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
            
            # Create the new tag
            tag = tag_base.replace("N", str(next_n))
            click.echo(f"Creating new tag: {tag}")
            new_tag = repo.create_tag(tag, message=f"Release {tag}")
            click.echo(f"Tag {tag} created successfully")
        
        # Check if the tag exists
        try:
            repo.tags[tag]
        except IndexError:
            click.echo(f"Tag '{tag}' not found in the repository.")
            return
        
        # Get the commit associated with the tag
        tag_commit = repo.tags[tag].commit
        
        # Check if local branch is outdated
        remote_refs = {}
        for remote in repo.remotes:
            try:
                remote_refs.update(remote.refs)
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
        
        # Get all commits after the tag
        commits_after_tag = list(repo.iter_commits(f"{tag}..HEAD"))
        
        # Check if there are any commits after the tag
        if not commits_after_tag:
            click.echo(f"Error: No commits found after tag '{tag}'.")
            click.echo("There's nothing to release. Create new commits before making a release.")
            return
        
        # Extract ticket names from commit messages
        ticket_pattern = get_ticket_pattern()
        ticket_regex = re.compile(ticket_pattern)
        tickets = set()
        
        for commit in commits_after_tag:
            commit_message = commit.message.strip()
            matches = ticket_regex.findall(commit_message)
            tickets.update(matches)
        
        # Get the commit message for the tag
        tag_commit_message = tag_commit.message.strip()
        
        click.echo(f"\nPreparing release for tag: {tag}")
        click.echo(f"Commit: {tag_commit.hexsha}")
        click.echo(f"Commit message: {tag_commit_message}")
        
        # Display ticket information
        if tickets:
            click.echo("\nHere is the list of tickets that were merged after last release:")
            for ticket in sorted(tickets):
                click.echo(f"- {ticket}")
        else:
            click.echo("\nNo tickets found in commits after the last release.")
        
        # Get project name from repository
        try:
            project_name = os.path.basename(os.path.normpath(repo.working_dir))
            # Check if there's an alias for this project
            project_aliases = get_project_aliases()
            if project_name in project_aliases:
                project_name = project_aliases[project_name]
        except:
            project_name = "Unknown Project"
        
        # Determine message format to use
        format_to_use = message_format if message_format else get_message_format()
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
        tickets_list = ""
        if tickets:
            if format_to_use == 'markdown':
                tickets_list = "\n".join([f"- {ticket}" for ticket in sorted(tickets)])
            else:
                tickets_list = "\n".join([f"- {ticket}" for ticket in sorted(tickets)])
        else:
            tickets_list = "No tickets found in this release."
        
        # Replace placeholders in template
        release_message = template_content
        release_message = release_message.replace("[PROJECT_NAME]", project_name)
        release_message = release_message.replace("[TAG_NAME]", tag)
        release_message = release_message.replace("[TICKETS_LIST]", tickets_list)
        
        click.echo("\nGenerated Release Message:")
        click.echo("==========================")
        click.echo(release_message)
        click.echo("==========================")
        
        click.echo("\nTo create a GitHub release, use the following information:")
        click.echo(f"Tag: {tag}")
        click.echo(f"Title: Release {tag}")
        click.echo(f"Description: Use the generated release message above")
        
    except git.exc.InvalidGitRepositoryError:
        click.echo("Current directory is not a git repository.")
    except Exception as e:
        click.echo(f"An error occurred: {str(e)}")

if __name__ == '__main__':
    main()