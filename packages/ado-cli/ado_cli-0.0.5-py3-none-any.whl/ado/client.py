import base64
from typing import Any, Dict, Optional
from urllib.parse import quote

import httpx


class AdoClient:
    """Azure DevOps Server API client"""

    def __init__(self, server_url: str, pat: str, collection: str):
        self.server_url = server_url.rstrip("/")
        self.collection = collection
        self.base_url = f"{self.server_url}/{quote(collection)}"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {self._encode_pat(pat)}",
        }

    def _encode_pat(self, pat: str) -> str:
        """Encode PAT for basic auth"""
        return base64.b64encode(f":{pat}".encode()).decode()

    def _request(self, method: str, url: str, **kwargs) -> httpx.Response:
        """Make API request"""
        with httpx.Client() as client:
            response = client.request(method, url, headers=self.headers, **kwargs)
            response.raise_for_status()
            return response

    def get_projects(self) -> Dict[str, Any]:
        """Get all projects"""
        url = f"{self.base_url}/_apis/projects?api-version=6.0"
        return self._request("GET", url).json()

    def get_repos(self, project: str) -> Dict[str, Any]:
        """Get repositories in a project"""
        url = f"{self.base_url}/{quote(project)}/_apis/git/repositories?api-version=6.0"
        return self._request("GET", url).json()

    def get_pull_requests(
        self, project: str, repo: str, status: str = "active"
    ) -> Dict[str, Any]:
        """Get pull requests"""
        url = f"{self.base_url}/{quote(project)}/_apis/git/repositories/{quote(repo)}/pullrequests?searchCriteria.status={status}&api-version=6.0"
        return self._request("GET", url).json()

    def get_pull_request(self, project: str, repo: str, pr_id: int) -> Dict[str, Any]:
        """Get specific pull request"""
        url = f"{self.base_url}/{quote(project)}/_apis/git/repositories/{quote(repo)}/pullrequests/{pr_id}?api-version=6.0"
        return self._request("GET", url).json()

    def create_pull_request(
        self, project: str, repo: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a pull request"""
        url = f"{self.base_url}/{quote(project)}/_apis/git/repositories/{quote(repo)}/pullrequests?api-version=6.0"
        return self._request("POST", url, json=data).json()

    def update_pull_request(
        self, project: str, repo: str, pr_id: int, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a pull request"""
        url = f"{self.base_url}/{quote(project)}/_apis/git/repositories/{quote(repo)}/pullrequests/{pr_id}?api-version=6.0"
        return self._request("PATCH", url, json=data).json()

    def create_pull_request_reviewer(
        self, project: str, repo: str, pr_id: int, reviewer_id: str
    ) -> Dict[str, Any]:
        """Add a reviewer to a pull request"""
        url = f"{self.base_url}/{quote(project)}/_apis/git/repositories/{quote(repo)}/pullrequests/{pr_id}/reviewers/{reviewer_id}?api-version=6.0"
        return self._request("PUT", url, json={}).json()

    def create_pull_request_thread(
        self, project: str, repo: str, pr_id: int, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a thread (review comment) on a pull request"""
        url = f"{self.base_url}/{quote(project)}/_apis/git/repositories/{quote(repo)}/pullrequests/{pr_id}/threads?api-version=6.0"
        return self._request("POST", url, json=data).json()

    def get_work_items(self, project: str, wiql: str) -> Dict[str, Any]:
        """Query work items"""
        url = f"{self.base_url}/{quote(project)}/_apis/wit/wiql?api-version=6.0"
        return self._request("POST", url, json={"query": wiql}).json()

    def get_work_item(self, work_item_id: int) -> Dict[str, Any]:
        """Get specific work item"""
        url = f"{self.base_url}/_apis/wit/workitems/{work_item_id}?api-version=6.0"
        return self._request("GET", url).json()

    def create_work_item(
        self, project: str, work_item_type: str, data: list
    ) -> Dict[str, Any]:
        """Create a work item"""
        url = f"{self.base_url}/{quote(project)}/_apis/wit/workitems/${work_item_type}?api-version=6.0"
        headers = {**self.headers, "Content-Type": "application/json-patch+json"}
        with httpx.Client() as client:
            response = client.patch(url, headers=headers, json=data)
            response.raise_for_status()
            return response.json()

    def get_definitions(self, project: str) -> Dict[str, Any]:
        """Get build definitions (pipelines)"""
        url = (
            f"{self.base_url}/{quote(project)}/_apis/build/definitions?api-version=6.0"
        )
        return self._request("GET", url).json()

    def get_builds(
        self,
        project: str,
        definition_id: Optional[int] = None,
        top: int = 50,
        branch_name: Optional[str] = None,
        reason_filter: Optional[str] = None,
        repository_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get builds (pipeline runs)"""
        url = f"{self.base_url}/{quote(project)}/_apis/build/builds?api-version=6.0&$top={top}"
        if definition_id:
            url += f"&definitions={definition_id}"
        if branch_name:
            url += f"&branchName={quote(branch_name)}"
        if reason_filter:
            url += f"&reasonFilter={reason_filter}"
        if repository_id:
            url += f"&repositoryId={repository_id}"
        return self._request("GET", url).json()

    def get_build(self, project: str, build_id: int) -> Dict[str, Any]:
        """Get specific build"""
        url = f"{self.base_url}/{quote(project)}/_apis/build/builds/{build_id}?api-version=6.0"
        return self._request("GET", url).json()

    def get_build_logs(self, project: str, build_id: int) -> Dict[str, Any]:
        """Get list of all logs for a build"""
        url = f"{self.base_url}/{quote(project)}/_apis/build/builds/{build_id}/logs?api-version=6.0"
        return self._request("GET", url).json()

    def get_build_log(self, project: str, build_id: int, log_id: int) -> str:
        """Get build log"""
        url = f"{self.base_url}/{quote(project)}/_apis/build/builds/{build_id}/logs/{log_id}?api-version=6.0"
        return self._request("GET", url).text

    def queue_build(
        self, project: str, definition_id: int, branch: Optional[str] = None
    ) -> Dict[str, Any]:
        """Queue a new build"""
        data = {"definition": {"id": definition_id}}
        if branch:
            data["sourceBranch"] = (
                branch if branch.startswith("refs/") else f"refs/heads/{branch}"
            )

        url = f"{self.base_url}/{quote(project)}/_apis/build/builds?api-version=6.0"
        return self._request("POST", url, json=data).json()

    def get_commit_diff(
        self, project: str, repo: str, base: str, target: str
    ) -> Dict[str, Any]:
        """Get diff between two commits"""
        url = f"{self.base_url}/{quote(project)}/_apis/git/repositories/{quote(repo)}/diffs/commits?baseVersion={base}&targetVersion={target}&api-version=6.0"
        return self._request("GET", url).json()
