"""GitHub organization tools for Point-Topic."""

from typing import Optional
from mcp.server.fastmcp import Context
from mcp.server.session import ServerSession
from point_topic_mcp.core.utils import check_env_vars
from dotenv import load_dotenv
import os
import json

load_dotenv()

ORG_NAME = "Point-Topic"

if check_env_vars('github_tools', ['GITHUB_TOKEN']):
    
    def _gh():
        """Get GitHub client."""
        from github import Github
        return Github(os.getenv("GITHUB_TOKEN"))
    
    def _fmt_issue(issue) -> dict:
        """Format issue data."""
        return {
            "number": issue.number,
            "title": issue.title,
            "state": issue.state,
            "url": issue.html_url,
            "repository": issue.repository.full_name,
            "author": issue.user.login,
            "created": issue.created_at.isoformat(),
            "labels": [l.name for l in issue.labels],
            "assignees": [a.login for a in issue.assignees],
        }

    def general_info() -> None:
        """
        These tools are used to interact with the Point-Topic GitHub organization.
        They can be used only by Admins.
        They are used to provide information on the Point Topic systems, as all our codebases are hosted here.
        They are used to search for issues and pull requests, create issues and pull requests,
        add comments to issues and pull requests, update issues and pull requests,
        and read file contents from repositories.

        Some of the most relevant repositories are:
        - UPC_Core (the dbt pipeline for the core UPC datasets)
        - UPC_Client (the dbt pipeline for delivering outputs to everywhere)
        - upc_query_agent (the MCP Client application)
        - point-topic-mcp (this repository)
 
        This function is only for displaying some general information to the agent via the docstring

        Returns: None
        """
        return None
    
    def search_issues(
        query: str = "",
        repo: str = "",
        state: str = "open",
        labels: str = "",
        assignee: str = "",
        type: str = "issue",
        max_results: int = 30,
        ctx: Optional[Context[ServerSession, None]] = None
    ) -> str:
        """Search issues and/or PRs in Point-Topic organization by keyword, label, assignee, etc.
        
        Args:
            query: Search text (e.g. "bug in API", "performance", "regression")
            repo: Limit to repo name (e.g. "point-topic-mcp", "UPC_Core")
                  Leave empty to search all repos in the organization
            state: Filter by state - "open" (default), "closed", or "all"
            labels: Comma-separated label names (e.g. "bug,urgent")
                   Results must have ALL specified labels
            assignee: Filter by assignee GitHub username
            type: What to search - "issue" (default), "pr", or "both"
                 NOTE: type="both" may not work due to GitHub API constraints (requires explicit filter)
                       For searching both, use separate queries with type="issue" and type="pr"
            max_results: Maximum results to return (default 30)
        
        Returns: JSON object with count and list of matching issues/PRs
        
        Key repos to search: UPC_Core, UPC_Client, upc_query_agent, point-topic-mcp
        
        Example: Find open bugs in point-topic-mcp repo
            query: "error", repo: "point-topic-mcp", state: "open", labels: "bug"
        """
        try:
            g = _gh()
            parts = [f"org:{ORG_NAME}"]
            
            # GitHub requires is:issue or is:pull-request
            if type == "pr":
                parts.append("is:pull-request")
            elif type == "both":
                pass  # search both by not specifying
            else:
                parts.append("is:issue")
            
            if query: parts.append(query)
            if repo: 
                parts.append(f"repo:{ORG_NAME}/{repo}" if "/" not in repo else f"repo:{repo}")
            if state != "all": parts.append(f"state:{state}")
            if labels:
                for l in labels.split(","): parts.append(f"label:{l.strip()}")
            if assignee: parts.append(f"assignee:{assignee}")
            
            results = [_fmt_issue(i) for i, _ in zip(g.search_issues(" ".join(parts)), range(max_results))]
            return json.dumps({"count": len(results), "issues": results}, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, indent=2)
    
    def get_issue(
        repo: str,
        number: int,
        with_comments: bool = True,
        ctx: Optional[Context[ServerSession, None]] = None
    ) -> str:
        """Get full issue/PR details with body and comments.
        
        Args:
            repo: Repo name (e.g. "point-topic-mcp", "UPC_Core")
            number: Issue/PR number
            with_comments: Include comments (default True)
        """
        try:
            g = _gh()
            repo_name = f"{ORG_NAME}/{repo}" if "/" not in repo else repo
            issue = g.get_repo(repo_name).get_issue(number)
            
            result = _fmt_issue(issue)
            result["body"] = issue.body
            
            if with_comments and issue.comments > 0:
                result["comments"] = [{
                    "author": c.user.login,
                    "body": c.body,
                    "created": c.created_at.isoformat()
                } for c in issue.get_comments()]
            
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, indent=2)
    
    def list_repos(
        language: str = "",
        max_results: int = 50,
        ctx: Optional[Context[ServerSession, None]] = None
    ) -> str:
        """List Point-Topic organization repositories.
        
        Args:
            language: Filter by language (e.g. "Python")
            max_results: Max results (default 50)
        """
        try:
            g = _gh()
            org = g.get_organization(ORG_NAME)
            results = []
            
            for i, repo in enumerate(org.get_repos()):
                if i >= max_results: break
                if language and repo.language != language: continue
                
                results.append({
                    "name": repo.name,
                    "description": repo.description,
                    "url": repo.html_url,
                    "language": repo.language,
                    "private": repo.private,
                    "default_branch": repo.default_branch,
                    "open_issues": repo.open_issues_count,
                    "updated": repo.updated_at.isoformat(),
                })
            
            return json.dumps({"count": len(results), "repos": results}, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, indent=2)
    
    def get_repo(
        repo: str,
        ctx: Optional[Context[ServerSession, None]] = None
    ) -> str:
        """Get repository details including branches.
        
        Args:
            repo: Repo name
        """
        try:
            g = _gh()
            repo_name = f"{ORG_NAME}/{repo}" if "/" not in repo else repo
            r = g.get_repo(repo_name)
            
            return json.dumps({
                "name": r.name,
                "description": r.description,
                "url": r.html_url,
                "language": r.language,
                "default_branch": r.default_branch,
                "branches": [{"name": b.name, "protected": b.protected} for b in r.get_branches()],
                "topics": r.get_topics(),
                "stats": {
                    "stars": r.stargazers_count,
                    "forks": r.forks_count,
                    "open_issues": r.open_issues_count,
                }
            }, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, indent=2)
    
    def read_file(
        repo: str,
        path: str,
        branch: str = "",
        ctx: Optional[Context[ServerSession, None]] = None
    ) -> str:
        """Read file/directory contents from repo. Returns file text or JSON list of dir contents.
        
        Args:
            repo: Repo name (e.g. "point-topic-mcp", "UPC_Core")
            path: File path (e.g. "src/main.py") or directory path (e.g. "src/")
            branch: Branch name (default: repo default branch)
        """
        try:
            g = _gh()
            repo_name = f"{ORG_NAME}/{repo}" if "/" not in repo else repo
            r = g.get_repo(repo_name)
            ref = branch or r.default_branch
            
            contents = r.get_contents(path, ref=ref)
            
            # If it's a file
            if hasattr(contents, 'decoded_content'):
                return contents.decoded_content.decode('utf-8')
            
            # If it's a directory
            if isinstance(contents, list):
                items = [{
                    "name": item.name,
                    "path": item.path,
                    "type": item.type,
                    "size": item.size if item.type == "file" else None
                } for item in contents]
                return json.dumps({"path": path, "items": items}, indent=2)
            
            return "Error: Unexpected content type"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def search_code(
        query: str,
        repo: str = "",
        language: str = "",
        max_results: int = 30,
        ctx: Optional[Context[ServerSession, None]] = None
    ) -> str:
        """Search code across Point-Topic repos. Returns file paths and URLs.
        
        Args:
            query: Code to search for (e.g. "def calculate_total", "class User")
            repo: Limit to repo (e.g. "point-topic-mcp")
            language: Filter by language (e.g. "Python", "SQL")
            max_results: Max results (default 30)
        """
        try:
            g = _gh()
            parts = [query, f"org:{ORG_NAME}"]
            if language: parts.append(f"language:{language}")
            if repo:
                repo_name = f"{ORG_NAME}/{repo}" if "/" not in repo else repo
                parts.append(f"repo:{repo_name}")
            
            results = [{
                "repo": code.repository.full_name,
                "path": code.path,
                "url": code.html_url
            } for code, _ in zip(g.search_code(" ".join(parts)), range(max_results))]
            
            return json.dumps({"count": len(results), "results": results}, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, indent=2)
    
    def get_commits(
        repo: str,
        branch: str = "",
        author: str = "",
        max_results: int = 20,
        ctx: Optional[Context[ServerSession, None]] = None
    ) -> str:
        """Get commit history for repository.
        
        Args:
            repo: Repo name
            branch: Branch name (optional)
            author: Filter by author (optional)
            max_results: Max results (default 20)
        """
        try:
            g = _gh()
            repo_name = f"{ORG_NAME}/{repo}" if "/" not in repo else repo
            r = g.get_repo(repo_name)
            
            kwargs = {}
            if branch: kwargs["sha"] = branch
            if author: kwargs["author"] = author
            
            commits = [{
                "sha": c.sha[:8],
                "message": c.commit.message.split("\n")[0],
                "author": c.commit.author.name,
                "date": c.commit.author.date.isoformat(),
                "url": c.html_url
            } for c, _ in zip(r.get_commits(**kwargs), range(max_results))]
            
            return json.dumps({"count": len(commits), "commits": commits}, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, indent=2)
    
    # SAFE WRITE OPERATIONS
    
    def create_issue(
        repo: str,
        title: str,
        body: str = "",
        labels: str = "",
        assignees: str = "",
        ctx: Optional[Context[ServerSession, None]] = None
    ) -> str:
        """Create new issue. SAFE: cannot modify/delete existing data.
        
        Args:
            repo: Repo name (e.g. "point-topic-mcp", "UPC_Core")
            title: Issue title
            body: Issue body (markdown supported)
            labels: Comma-separated (e.g. "bug,urgent")
            assignees: Comma-separated usernames
        """
        try:
            g = _gh()
            repo_name = f"{ORG_NAME}/{repo}" if "/" not in repo else repo
            r = g.get_repo(repo_name)
            
            kwargs = {"title": title, "body": body}
            if labels: kwargs["labels"] = [l.strip() for l in labels.split(",")]
            if assignees: kwargs["assignees"] = [a.strip() for a in assignees.split(",")]
            
            issue = r.create_issue(**kwargs)
            
            return json.dumps({
                "success": True,
                "number": issue.number,
                "url": issue.html_url
            }, indent=2)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)}, indent=2)
    
    def create_pr(
        repo: str,
        title: str,
        head: str,
        base: str = "",
        body: str = "",
        draft: bool = False,
        ctx: Optional[Context[ServerSession, None]] = None
    ) -> str:
        """Create a pull request from an existing branch.
        
        IMPORTANT LIMITATION: Cannot be used to make code changes. This tool only creates PRs
        from pre-existing branches that already have commits. The branch must be created and 
        committed to separately (e.g., by a human, git push, or propose_code_change tool).
        
        Use Cases:
        - Promote work-in-progress to PR after commits are already on a branch
        - Create PR from a branch someone else pushed
        - Create PR from a feature branch that already exists
        
        To make code changes and create a PR in one step, use propose_code_change instead.
        
        Args:
            repo: Repo name (e.g. "point-topic-mcp", "UPC_Core")
            title: PR title
            head: Source branch name (branch must already exist with commits)
            base: Target branch to merge into (default: repo default branch, usually "main")
            body: PR body/description (markdown supported)
            draft: Create as draft PR (default False)
        
        Returns: JSON with success status, PR number, and URL
        
        Example: Create PR to merge "feature/new-api" into "main"
            repo: "point-topic-mcp"
            title: "Add new API endpoint"
            head: "feature/new-api"
            base: "main"
            body: "Implements the new REST API endpoint for data export"
        """
        try:
            g = _gh()
            repo_name = f"{ORG_NAME}/{repo}" if "/" not in repo else repo
            r = g.get_repo(repo_name)
            
            pr = r.create_pull(
                title=title,
                body=body,
                head=head,
                base=base or r.default_branch,
                draft=draft
            )
            
            return json.dumps({
                "success": True,
                "number": pr.number,
                "url": pr.html_url
            }, indent=2)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)}, indent=2)
    
    def add_comment(
        repo: str,
        number: int,
        comment: str,
        ctx: Optional[Context[ServerSession, None]] = None
    ) -> str:
        """Add comment to issue/PR. SAFE: cannot modify/delete existing content.
        
        Args:
            repo: Repo name (e.g. "point-topic-mcp", "UPC_Core")
            number: Issue/PR number
            comment: Comment text (markdown supported)
        """
        try:
            g = _gh()
            repo_name = f"{ORG_NAME}/{repo}" if "/" not in repo else repo
            issue = g.get_repo(repo_name).get_issue(number)
            c = issue.create_comment(comment)
            
            return json.dumps({
                "success": True,
                "url": c.html_url
            }, indent=2)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)}, indent=2)
    
    def update_issue(
        repo: str,
        number: int,
        title: str = "",
        body: str = "",
        state: str = "",
        labels: str = "",
        ctx: Optional[Context[ServerSession, None]] = None
    ) -> str:
        """Update issue/PR title, body, state, or add labels. SAFE: cannot delete.
        
        Args:
            repo: Repo name (e.g. "point-topic-mcp", "UPC_Core")
            number: Issue/PR number
            title: New title (optional, leave empty to keep current)
            body: New body (optional, leave empty to keep current)
            state: "open" or "closed" (optional, leave empty to keep current)
            labels: Comma-separated labels to ADD (optional, doesn't remove existing)
        """
        try:
            g = _gh()
            repo_name = f"{ORG_NAME}/{repo}" if "/" not in repo else repo
            issue = g.get_repo(repo_name).get_issue(number)
            
            kwargs = {}
            if title: kwargs["title"] = title
            if body: kwargs["body"] = body
            if state in ["open", "closed"]: kwargs["state"] = state
            
            if kwargs:
                issue.edit(**kwargs)
            
            if labels:
                issue.add_to_labels(*[l.strip() for l in labels.split(",")])
            
            return json.dumps({
                "success": True,
                "url": issue.html_url
            }, indent=2)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)}, indent=2)
    
    def suggest_tool_improvement(
        tool_name: str,
        what_went_wrong: str,
        what_worked: str,
        suggested_fix: str = "",
        ctx: Optional[Context[ServerSession, None]] = None
    ) -> str:
        """Agent self-improvement: report confusing tool docs and suggest fixes.
        
        Use this when you tried a tool call that failed, then figured out the right way.
        Creates issue in point-topic-mcp repo with your feedback to improve docs.
        
        For code changes: use propose_code_change to directly create a PR with the fix.
        For other feedback: use this function to create an issue.
        
        Args:
            tool_name: MCP tool name (e.g. "search_issues", "execute_query", "read_file")
            what_went_wrong: Error/confusion you encountered (paste error message)
            what_worked: What eventually worked (paste successful approach)
            suggested_fix: Your suggested docstring improvement (optional)
        
        Example:
            After getting search_issues wrong then fixing it, call this to help improve docs.
        """
        try:
            from datetime import datetime, timezone
            
            g = _gh()
            repo = g.get_repo(f"{ORG_NAME}/point-topic-mcp")
            
            # Build issue body with sections
            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            
            body_parts = [
                "## Agent Feedback on Tool Documentation",
                "",
                f"**Tool:** `{tool_name}`",
                f"**Reported:** {timestamp}",
                "",
                "### What Went Wrong",
                "",
                "```",
                what_went_wrong,
                "```",
                "",
                "### What Worked",
                "",
                "```",
                what_worked,
                "```",
            ]
            
            if suggested_fix:
                body_parts.extend([
                    "",
                    "### Suggested Improvement",
                    "",
                    suggested_fix,
                ])
            
            body_parts.extend([
                "",
                "---",
                "*This issue was automatically created by an AI agent to help improve tool documentation.*"
            ])
            
            body = "\n".join(body_parts)
            title = f"[Agent Feedback] Improve `{tool_name}` documentation"
            
            # Create issue with labels
            issue = repo.create_issue(
                title=title,
                body=body,
                labels=["documentation", "agent-feedback"]
            )
            
            return json.dumps({
                "success": True,
                "message": "Thanks for helping improve the docs! Issue created.",
                "issue_number": issue.number,
                "url": issue.html_url
            }, indent=2)
            
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)}, indent=2)
    
    def propose_code_change(
        repo: str,
        file_path: str,
        old_content: str,
        new_content: str,
        change_description: str,
        ctx: Optional[Context[ServerSession, None]] = None
    ) -> str:
        """Propose code changes by editing files, committing, and creating PR automatically.
        
        THIS IS THE MAIN TOOL FOR CODE CHANGES. Use this to fix bugs, update docs, etc.
        Automatically commits to agent-dev branch and creates/updates PR for review.
        
        SAFE: Can only write to agent-dev branch. All changes reviewed before merge.
        Uses search/replace - only specify the lines changing (token efficient).
        
        Args:
            repo: Repo name (e.g. "point-topic-mcp", "UPC_Core")
            file_path: Path to file (e.g. "src/point_topic_mcp/tools/github_tools.py")
            old_content: Text to find and replace (must be unique in file)
            new_content: Text to replace it with
            change_description: What changed and why (used for commit msg and PR body)
        
        When to use: Anytime you want to change code/docs and create a PR.
        
        Example:
            propose_code_change(
                repo="point-topic-mcp",
                file_path="src/point_topic_mcp/tools/github_tools.py",
                old_content='        type: "issue" (default), "pr", or "both"',
                new_content='        type: "issue" (default) or "pr"',
                change_description="Fix search_issues docstring - remove unsupported 'both' option"
            )
        """
        try:
            g = _gh()
            repo_name = f"{ORG_NAME}/{repo}" if "/" not in repo else repo
            r = g.get_repo(repo_name)
            
            AGENT_BRANCH = "agent-dev"
            default_branch = r.default_branch
            
            # Ensure agent-dev branch exists
            try:
                r.get_branch(AGENT_BRANCH)
            except:
                # Branch doesn't exist, create it from default branch
                default_ref = r.get_git_ref(f"heads/{default_branch}")
                r.create_git_ref(f"refs/heads/{AGENT_BRANCH}", default_ref.object.sha)
            
            # Get current file from agent-dev branch
            try:
                file_contents = r.get_contents(file_path, ref=AGENT_BRANCH)
                current_content = file_contents.decoded_content.decode('utf-8')
                file_sha = file_contents.sha
            except:
                return json.dumps({
                    "success": False,
                    "error": f"File {file_path} not found in {AGENT_BRANCH} branch"
                }, indent=2)
            
            # Perform search and replace
            if old_content not in current_content:
                return json.dumps({
                    "success": False,
                    "error": f"old_content not found in file. Make sure it matches exactly (including whitespace)."
                }, indent=2)
            
            # Check if old_content appears multiple times
            if current_content.count(old_content) > 1:
                return json.dumps({
                    "success": False,
                    "error": f"old_content appears {current_content.count(old_content)} times in file. Must be unique."
                }, indent=2)
            
            # Do the replacement
            updated_content = current_content.replace(old_content, new_content)
            
            # Commit the change to agent-dev branch
            commit_message = change_description
            r.update_file(
                path=file_path,
                message=commit_message,
                content=updated_content,
                sha=file_sha,
                branch=AGENT_BRANCH
            )
            
            # Create PR from agent-dev to default branch
            pr_title = f"[Agent Proposal] {change_description[:50]}"
            pr_body = f"""## Agent-Proposed Code Change

{change_description}

**File Modified:** `{file_path}`

**Branch:** `{AGENT_BRANCH}`

---
*This PR was automatically created by an AI agent. Please review carefully before merging.*
"""
            
            # Check if PR already exists
            existing_prs = r.get_pulls(state="open", head=f"{ORG_NAME}:{AGENT_BRANCH}", base=default_branch)
            pr = None
            
            for existing_pr in existing_prs:
                # Update existing PR title/body
                existing_pr.edit(title=pr_title, body=pr_body)
                pr = existing_pr
                break
            
            if not pr:
                # Create new PR
                pr = r.create_pull(
                    title=pr_title,
                    body=pr_body,
                    head=AGENT_BRANCH,
                    base=default_branch
                )
                
                # Add labels
                try:
                    pr.add_to_labels("agent-generated", "needs-review")
                except:
                    # Labels might not exist, that's ok
                    pass
            
            return json.dumps({
                "success": True,
                "message": "Code change committed to agent-dev and PR created for review",
                "pr_number": pr.number,
                "pr_url": pr.html_url,
                "branch": AGENT_BRANCH
            }, indent=2)
            
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)}, indent=2)

