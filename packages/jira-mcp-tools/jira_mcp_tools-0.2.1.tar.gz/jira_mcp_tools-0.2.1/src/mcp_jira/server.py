import os
import json
import requests
from fastmcp import FastMCP, Context
from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional
from jira import JIRA

class JiraApiClient:
    def __init__(self, server_url, email, api_token):
        self.jira = JIRA(server=server_url, basic_auth=(email, api_token))
  
    async def get_jira_ticket_info(self, issue_key: str):
        """Get information about a JIRA issue."""
        try:
            # Check if we have a valid cached response
            issue = self.jira.issue(issue_key)
            # Get description
            description = issue.fields.description or "No description"
            
            # Get comments
            comments = []
            for comment in issue.fields.comment.comments:
                comments.append({
                    'author': comment.author.displayName,
                    'created': comment.created,
                    'body': comment.body
                })
            
            result = {
                'description': description,
                'comments': comments
            }

            #TODO: handle comments with images

            return json.dumps(result, indent=2)
            
        except requests.exceptions.RequestException as e:
            # Handle network errors, timeouts, etc.
            raise ValueError(f"Failed to connect to JIRA API: {str(e)}")
        except json.JSONDecodeError as e:
            # Handle malformed JSON responses
            raise ValueError(f"Failed to parse JIRA API response: {str(e)}")
        except Exception as e:
            raise ValueError(f"Failed to get JIRA info: {str(e)}")
        
    async def get_jira_ticket_attachments(self, issue_key: str):
        """Get the attachments of a JIRA issue."""
        try:
            issue = self.jira.issue(issue_key)
            attachments = []
            for attachment in issue.fields.attachment:
                attachments.append({
                    'filename': attachment.filename,
                    'content': attachment.get()
                })

            #TODO: handle pdf and and image attachments

            return attachments
        except requests.exceptions.RequestException as e:
            # Handle network errors, timeouts, etc.
            raise ValueError(f"Failed to connect to JIRA API: {str(e)}")
        except json.JSONDecodeError as e:
            # Handle malformed JSON responses
            raise ValueError(f"Failed to parse JIRA API response: {str(e)}")
        except Exception as e:
            raise ValueError(f"Failed to get JIRA info: {str(e)}")
    
    async def search_issues(self, jql: str, max_results: int = 50, fields: Optional[str] = None):
        """Search for issues using JQL (Jira Query Language)."""
        try:
            # Default fields if not specified
            if not fields:
                fields = "summary,status,assignee,priority,created,updated,duedate,labels,components"
            
            issues = self.jira.search_issues(jql, maxResults=max_results, fields=fields)
            
            results = []
            for issue in issues:
                issue_data = {
                    'key': issue.key,
                    'summary': issue.fields.summary,
                    'status': issue.fields.status.name,
                    'assignee': issue.fields.assignee.displayName if issue.fields.assignee else 'Unassigned',
                    'priority': issue.fields.priority.name if issue.fields.priority else 'None',
                    'created': issue.fields.created,
                    'updated': issue.fields.updated,
                    'duedate': issue.fields.duedate if hasattr(issue.fields, 'duedate') else None,
                    'labels': issue.fields.labels if hasattr(issue.fields, 'labels') else [],
                    'components': [c.name for c in issue.fields.components] if hasattr(issue.fields, 'components') else []
                }
                results.append(issue_data)
            
            return json.dumps({
                'total': len(results),
                'issues': results
            }, indent=2)
            
        except Exception as e:
            raise ValueError(f"Failed to search issues: {str(e)}")
    
    async def get_epic_details(self, epic_key: str):
        """Get detailed information about an epic including all child issues."""
        try:
            epic = self.jira.issue(epic_key)
            
            # Get all issues in this epic using JQL
            jql = f'"Epic Link" = {epic_key}'
            child_issues = self.jira.search_issues(jql, maxResults=1000)
            
            # Calculate progress metrics
            total_issues = len(child_issues)
            done_issues = sum(1 for issue in child_issues if issue.fields.status.name.lower() in ['done', 'closed', 'resolved'])
            in_progress = sum(1 for issue in child_issues if issue.fields.status.name.lower() in ['in progress', 'in review'])
            
            # Get story points if available
            total_points = 0
            done_points = 0
            for issue in child_issues:
                # Story points field varies by Jira instance (customfield_10016 is common)
                if hasattr(issue.fields, 'customfield_10016') and issue.fields.customfield_10016:
                    points = float(issue.fields.customfield_10016)
                    total_points += points
                    if issue.fields.status.name.lower() in ['done', 'closed', 'resolved']:
                        done_points += points
            
            # Build child issues list
            children = []
            for issue in child_issues:
                children.append({
                    'key': issue.key,
                    'summary': issue.fields.summary,
                    'status': issue.fields.status.name,
                    'assignee': issue.fields.assignee.displayName if issue.fields.assignee else 'Unassigned',
                    'type': issue.fields.issuetype.name
                })
            
            result = {
                'epic_key': epic_key,
                'epic_summary': epic.fields.summary,
                'epic_status': epic.fields.status.name,
                'description': epic.fields.description or 'No description',
                'total_issues': total_issues,
                'done_issues': done_issues,
                'in_progress_issues': in_progress,
                'todo_issues': total_issues - done_issues - in_progress,
                'completion_percentage': round((done_issues / total_issues * 100) if total_issues > 0 else 0, 1),
                'total_story_points': total_points,
                'done_story_points': done_points,
                'child_issues': children
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            raise ValueError(f"Failed to get epic details: {str(e)}")
    
    async def get_sprint_info(self, board_id: int, sprint_id: Optional[int] = None):
        """Get information about sprints on a board."""
        try:
            if sprint_id:
                # Get specific sprint
                sprint = self.jira.sprint(sprint_id)
                issues = self.jira.search_issues(f'sprint = {sprint_id}', maxResults=1000)
                
                sprint_data = {
                    'id': sprint.id,
                    'name': sprint.name,
                    'state': sprint.state,
                    'start_date': sprint.startDate if hasattr(sprint, 'startDate') else None,
                    'end_date': sprint.endDate if hasattr(sprint, 'endDate') else None,
                    'total_issues': len(issues),
                    'issues': []
                }
                
                for issue in issues:
                    sprint_data['issues'].append({
                        'key': issue.key,
                        'summary': issue.fields.summary,
                        'status': issue.fields.status.name,
                        'assignee': issue.fields.assignee.displayName if issue.fields.assignee else 'Unassigned'
                    })
                
                return json.dumps(sprint_data, indent=2)
            else:
                # Get all sprints for board
                sprints = self.jira.sprints(board_id)
                
                sprint_list = []
                for sprint in sprints:
                    sprint_list.append({
                        'id': sprint.id,
                        'name': sprint.name,
                        'state': sprint.state,
                        'start_date': sprint.startDate if hasattr(sprint, 'startDate') else None,
                        'end_date': sprint.endDate if hasattr(sprint, 'endDate') else None
                    })
                
                return json.dumps({
                    'board_id': board_id,
                    'total_sprints': len(sprint_list),
                    'sprints': sprint_list
                }, indent=2)
                
        except Exception as e:
            raise ValueError(f"Failed to get sprint info: {str(e)}")
    

    async def get_issue_history(self, issue_key: str):
        """Get the change history of a Jira issue."""
        try:
            issue = self.jira.issue(issue_key, expand='changelog')
            
            history = []
            for change in issue.changelog.histories:
                change_data = {
                    'author': change.author.displayName,
                    'created': change.created,
                    'changes': []
                }
                
                for item in change.items:
                    change_data['changes'].append({
                        'field': item.field,
                        'fieldtype': item.fieldtype,
                        'from': item.fromString,
                        'to': item.toString
                    })
                
                history.append(change_data)
            
            result = {
                'issue_key': issue_key,
                'summary': issue.fields.summary,
                'current_status': issue.fields.status.name,
                'history': history
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            raise ValueError(f"Failed to get issue history: {str(e)}")
    
    async def get_project_releases(self, project_key: str):
        """Get all releases/versions for a project."""
        try:
            versions = self.jira.project_versions(project_key)
            
            releases = []
            for version in versions:
                # Get issues for this version
                jql = f'project = {project_key} AND fixVersion = "{version.name}"'
                issues = self.jira.search_issues(jql, maxResults=1000)
                
                release_data = {
                    'id': version.id,
                    'name': version.name,
                    'description': version.description if hasattr(version, 'description') else None,
                    'released': version.released if hasattr(version, 'released') else False,
                    'release_date': version.releaseDate if hasattr(version, 'releaseDate') else None,
                    'start_date': version.startDate if hasattr(version, 'startDate') else None,
                    'archived': version.archived if hasattr(version, 'archived') else False,
                    'total_issues': len(issues),
                    'issues': []
                }
                
                # Add issue summaries
                for issue in issues[:50]:  # Limit to first 50 issues
                    release_data['issues'].append({
                        'key': issue.key,
                        'summary': issue.fields.summary,
                        'status': issue.fields.status.name,
                        'type': issue.fields.issuetype.name
                    })
                
                releases.append(release_data)
            
            return json.dumps({
                'project_key': project_key,
                'total_releases': len(releases),
                'releases': releases
            }, indent=2)
            
        except Exception as e:
            raise ValueError(f"Failed to get project releases: {str(e)}")
    
    async def get_issue_links(self, issue_key: str):
        """Get all linked issues for a given issue."""
        try:
            issue = self.jira.issue(issue_key)
            
            links = []
            if hasattr(issue.fields, 'issuelinks'):
                for link in issue.fields.issuelinks:
                    link_data = {
                        'type': link.type.name,
                        'direction': None,
                        'linked_issue': {}
                    }
                    
                    # Determine direction and get linked issue
                    if hasattr(link, 'outwardIssue'):
                        link_data['direction'] = 'outward'
                        linked = link.outwardIssue
                    elif hasattr(link, 'inwardIssue'):
                        link_data['direction'] = 'inward'
                        linked = link.inwardIssue
                    else:
                        continue
                    
                    link_data['linked_issue'] = {
                        'key': linked.key,
                        'summary': linked.fields.summary,
                        'status': linked.fields.status.name,
                        'type': linked.fields.issuetype.name
                    }
                    
                    links.append(link_data)
            
            result = {
                'issue_key': issue_key,
                'summary': issue.fields.summary,
                'total_links': len(links),
                'links': links
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            raise ValueError(f"Failed to get issue links: {str(e)}")
    
    async def add_comment(self, issue_key: str, comment_text: str):
        """Add a comment to a Jira issue."""
        try:
            issue = self.jira.issue(issue_key)
            comment = self.jira.add_comment(issue, comment_text)
            
            result = {
                'issue_key': issue_key,
                'comment_id': comment.id,
                'author': comment.author.displayName,
                'created': comment.created,
                'body': comment.body
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            raise ValueError(f"Failed to add comment: {str(e)}")
    
    async def update_issue(self, issue_key: str, fields: dict):
        """Update fields of a Jira issue."""
        try:
            issue = self.jira.issue(issue_key)
            issue.update(fields=fields)
            
            # Get updated issue
            updated_issue = self.jira.issue(issue_key)
            
            result = {
                'issue_key': issue_key,
                'summary': updated_issue.fields.summary,
                'status': updated_issue.fields.status.name,
                'updated': updated_issue.fields.updated,
                'updated_fields': list(fields.keys())
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            raise ValueError(f"Failed to update issue: {str(e)}")
    
    async def create_issue(self, project_key: str, summary: str, description: str, issue_type: str = "Task"):
        """Create a new Jira issue."""
        try:
            issue_dict = {
                'project': {'key': project_key},
                'summary': summary,
                'description': description,
                'issuetype': {'name': issue_type}
            }
            
            new_issue = self.jira.create_issue(fields=issue_dict)
            
            result = {
                'issue_key': new_issue.key,
                'summary': new_issue.fields.summary,
                'status': new_issue.fields.status.name,
                'issue_type': new_issue.fields.issuetype.name,
                'created': new_issue.fields.created,
                'url': f"{self.jira._options['server']}/browse/{new_issue.key}"
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            raise ValueError(f"Failed to create issue: {str(e)}")
    
    async def transition_issue(self, issue_key: str, transition_name: str):
        """Transition a Jira issue to a new status."""
        try:
            issue = self.jira.issue(issue_key)
            
            # Get available transitions
            transitions = self.jira.transitions(issue)
            transition_id = None
            
            for t in transitions:
                if t['name'].lower() == transition_name.lower():
                    transition_id = t['id']
                    break
            
            if not transition_id:
                available = [t['name'] for t in transitions]
                raise ValueError(f"Transition '{transition_name}' not found. Available: {', '.join(available)}")
            
            # Perform transition
            self.jira.transition_issue(issue, transition_id)
            
            # Get updated issue
            updated_issue = self.jira.issue(issue_key)
            
            result = {
                'issue_key': issue_key,
                'summary': updated_issue.fields.summary,
                'old_status': issue.fields.status.name,
                'new_status': updated_issue.fields.status.name,
                'transition': transition_name
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            raise ValueError(f"Failed to transition issue: {str(e)}")
    
    async def assign_issue(self, issue_key: str, assignee: str):
        """Assign a Jira issue to a user."""
        try:
            issue = self.jira.issue(issue_key)
            old_assignee = issue.fields.assignee.displayName if issue.fields.assignee else 'Unassigned'
            
            # Assign issue (use None for unassign, or username/email)
            if assignee.lower() in ['none', 'unassigned', '']:
                self.jira.assign_issue(issue, None)
                new_assignee = 'Unassigned'
            else:
                self.jira.assign_issue(issue, assignee)
                updated_issue = self.jira.issue(issue_key)
                new_assignee = updated_issue.fields.assignee.displayName if updated_issue.fields.assignee else 'Unassigned'
            
            result = {
                'issue_key': issue_key,
                'summary': issue.fields.summary,
                'old_assignee': old_assignee,
                'new_assignee': new_assignee
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            raise ValueError(f"Failed to assign issue: {str(e)}")

class JiraContext:
    def __init__(self, connector: JiraApiClient):
        self.connector = connector

@asynccontextmanager
async def server_lifespan(server: FastMCP) -> AsyncIterator[JiraContext]:
    """Manage application lifecycle for Jira Api Client."""
    jira_url = os.getenv("JIRA_URL")
    jira_email = os.getenv("JIRA_EMAIL")
    jira_token = os.getenv("JIRA_TOKEN")
    connector = JiraApiClient(jira_url, jira_email, jira_token)

    try:
        yield JiraContext(connector)
    finally:
        pass

mcp = FastMCP(name="JIRA", lifespan=server_lifespan)

@mcp.tool()
async def get_jira_ticket_info(issue_key: str, ctx: Context) -> str:
    """Get detailed information about a JIRA issue."""
    if not issue_key:
        return "Error: Missing required parameter 'issue_key'"
    
    connector = ctx.request_context.lifespan_context.connector
    try:
        return await connector.get_jira_ticket_info(issue_key)
    except ValueError as e:
        return f"Error: {str(e)}"
    
@mcp.tool()
async def get_jira_ticket_attachments(issue_key: str, ctx: Context) -> str:
    """Get the attachments of a JIRA issue."""
    if not issue_key:
        return "Error: Missing required parameter 'issue_key'"
    
    connector = ctx.request_context.lifespan_context.connector
    try:
        return await connector.get_jira_ticket_attachments(issue_key)
    except ValueError as e:
        return f"Error: {str(e)}"

@mcp.tool()
async def search_issues(jql: str, max_results: int = 50, fields: Optional[str] = None, ctx: Context = None) -> str:
    """Search for Jira issues using JQL (Jira Query Language).
    
    Args:
        jql: JQL query string (e.g., 'project = PROJ AND status = "In Progress"')
        max_results: Maximum number of results to return (default: 50)
        fields: Comma-separated list of fields to return (default: summary,status,assignee,priority,created,updated,duedate,labels,components)
    
    Examples:
        - 'project = MYPROJ'
        - 'assignee = currentUser() AND status != Done'
        - 'updated >= -7d ORDER BY updated DESC'
        - 'labels = urgent AND duedate < now()'
    """
    if not jql:
        return "Error: Missing required parameter 'jql'"
    
    connector = ctx.request_context.lifespan_context.connector
    try:
        return await connector.search_issues(jql, max_results, fields)
    except ValueError as e:
        return f"Error: {str(e)}"

@mcp.tool()
async def get_epic_details(epic_key: str, ctx: Context) -> str:
    """Get detailed information about an epic including all child issues and progress metrics.
    
    Args:
        epic_key: The epic issue key (e.g., 'PROJ-123')
    
    Returns:
        Epic summary, status, description, child issues, completion percentage, and story points
    """
    if not epic_key:
        return "Error: Missing required parameter 'epic_key'"
    
    connector = ctx.request_context.lifespan_context.connector
    try:
        return await connector.get_epic_details(epic_key)
    except ValueError as e:
        return f"Error: {str(e)}"

@mcp.tool()
async def get_sprint_info(board_id: int, sprint_id: Optional[int] = None, ctx: Context = None) -> str:
    """Get information about sprints on a Jira board.
    
    Args:
        board_id: The Jira board ID
        sprint_id: Optional specific sprint ID. If not provided, returns all sprints for the board
    
    Returns:
        Sprint details including name, state, dates, and issues (if sprint_id provided)
        or list of all sprints (if sprint_id not provided)
    """
    if not board_id:
        return "Error: Missing required parameter 'board_id'"
    
    connector = ctx.request_context.lifespan_context.connector
    try:
        return await connector.get_sprint_info(board_id, sprint_id)
    except ValueError as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def get_issue_history(issue_key: str, ctx: Context) -> str:
    """Get the change history of a Jira issue.
    
    Args:
        issue_key: The issue key (e.g., 'PROJ-123')
    
    Returns:
        Complete change history including status transitions, assignee changes, and field updates
    """
    if not issue_key:
        return "Error: Missing required parameter 'issue_key'"
    
    connector = ctx.request_context.lifespan_context.connector
    try:
        return await connector.get_issue_history(issue_key)
    except ValueError as e:
        return f"Error: {str(e)}"

@mcp.tool()
async def get_project_releases(project_key: str, ctx: Context) -> str:
    """Get all releases/versions for a project.
    
    Args:
        project_key: The project key (e.g., 'PROJ')
    
    Returns:
        List of all releases with their status, dates, and associated issues
    """
    if not project_key:
        return "Error: Missing required parameter 'project_key'"
    
    connector = ctx.request_context.lifespan_context.connector
    try:
        return await connector.get_project_releases(project_key)
    except ValueError as e:
        return f"Error: {str(e)}"

@mcp.tool()
async def get_issue_links(issue_key: str, ctx: Context) -> str:
    """Get all linked issues for a given issue.
    
    Args:
        issue_key: The issue key (e.g., 'PROJ-123')
    
    Returns:
        All issue links including blocks/blocked by, relates to, and other link types
    """
    if not issue_key:
        return "Error: Missing required parameter 'issue_key'"
    
    connector = ctx.request_context.lifespan_context.connector
    try:
        return await connector.get_issue_links(issue_key)
    except ValueError as e:
        return f"Error: {str(e)}"

@mcp.tool()
async def add_comment(issue_key: str, comment_text: str, ctx: Context) -> str:
    """Add a comment to a Jira issue.
    
    Args:
        issue_key: The issue key (e.g., 'PROJ-123')
        comment_text: The comment text to add
    
    Returns:
        Comment details including ID, author, and timestamp
    """
    if not issue_key or not comment_text:
        return "Error: Missing required parameters 'issue_key' and 'comment_text'"
    
    connector = ctx.request_context.lifespan_context.connector
    try:
        return await connector.add_comment(issue_key, comment_text)
    except ValueError as e:
        return f"Error: {str(e)}"

@mcp.tool()
async def update_issue(issue_key: str, fields: dict, ctx: Context) -> str:
    """Update fields of a Jira issue.
    
    Args:
        issue_key: The issue key (e.g., 'PROJ-123')
        fields: Dictionary of fields to update (e.g., {'summary': 'New title', 'description': 'New desc'})
    
    Returns:
        Updated issue details
    
    Examples:
        - Update summary: {'summary': 'New title'}
        - Update description: {'description': 'New description'}
        - Update priority: {'priority': {'name': 'High'}}
        - Update labels: {'labels': ['bug', 'urgent']}
    """
    if not issue_key or not fields:
        return "Error: Missing required parameters 'issue_key' and 'fields'"
    
    connector = ctx.request_context.lifespan_context.connector
    try:
        return await connector.update_issue(issue_key, fields)
    except ValueError as e:
        return f"Error: {str(e)}"

@mcp.tool()
async def create_issue(project_key: str, summary: str, description: str, issue_type: str = "Task", ctx: Context = None) -> str:
    """Create a new Jira issue.
    
    Args:
        project_key: The project key (e.g., 'PROJ')
        summary: Issue title/summary
        description: Issue description
        issue_type: Type of issue (default: 'Task', options: 'Bug', 'Story', 'Epic', etc.)
    
    Returns:
        Created issue details including key and URL
    """
    if not project_key or not summary or not description:
        return "Error: Missing required parameters 'project_key', 'summary', and 'description'"
    
    connector = ctx.request_context.lifespan_context.connector
    try:
        return await connector.create_issue(project_key, summary, description, issue_type)
    except ValueError as e:
        return f"Error: {str(e)}"

@mcp.tool()
async def transition_issue(issue_key: str, transition_name: str, ctx: Context) -> str:
    """Transition a Jira issue to a new status.
    
    Args:
        issue_key: The issue key (e.g., 'PROJ-123')
        transition_name: Name of the transition (e.g., 'In Progress', 'Done', 'To Do')
    
    Returns:
        Transition details including old and new status
    
    Note: Available transitions depend on the workflow. If transition fails,
    the error will list available transitions for the issue.
    """
    if not issue_key or not transition_name:
        return "Error: Missing required parameters 'issue_key' and 'transition_name'"
    
    connector = ctx.request_context.lifespan_context.connector
    try:
        return await connector.transition_issue(issue_key, transition_name)
    except ValueError as e:
        return f"Error: {str(e)}"

@mcp.tool()
async def assign_issue(issue_key: str, assignee: str, ctx: Context) -> str:
    """Assign a Jira issue to a user.
    
    Args:
        issue_key: The issue key (e.g., 'PROJ-123')
        assignee: Username or email of assignee (use 'none' or 'unassigned' to unassign)
    
    Returns:
        Assignment details including old and new assignee
    """
    if not issue_key or not assignee:
        return "Error: Missing required parameters 'issue_key' and 'assignee'"
    
    connector = ctx.request_context.lifespan_context.connector
    try:
        return await connector.assign_issue(issue_key, assignee)
    except ValueError as e:
        return f"Error: {str(e)}"

def main():
    mcp.run()

if __name__ == "__main__":
    main()
