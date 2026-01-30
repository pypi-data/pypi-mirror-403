
from ..steps.api import ApiStep

class GitHub:
    @staticmethod
    def get_repo(owner: str, repo: str, output: str = None):
        """Get repository details."""
        # Auto-inject secret if available in context? 
        # Steps resolve variables at runtime. So we just put the template string.
        # User must ensure {secrets:github_token} works or passed in context.
        return ApiStep(
            name=output or f"github_repo_{repo}",
            method="GET",
            url=f"https://api.github.com/repos/{owner}/{repo}",
            headers={
                "Authorization": "Bearer {secrets:github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
        )

    @staticmethod
    def list_issues(owner: str, repo: str, state: str = "open", output: str = None):
        """List repository issues."""
        return ApiStep(
            name=output or f"github_issues_{repo}",
            method="GET",
            url=f"https://api.github.com/repos/{owner}/{repo}/issues?state={state}",
            headers={
                "Authorization": "Bearer {secrets:github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
        )
