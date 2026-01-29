from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import threading
import time
from urllib.parse import urlparse, parse_qs


class MockAzureDevOpsHandler(BaseHTTPRequestHandler):
    """Mock HTTP handler for Azure DevOps API endpoints"""

    # In-memory storage
    projects = []
    repositories = {}
    pull_requests = {}
    work_items = {}
    next_pr_id = 1
    next_wi_id = 1000

    def log_message(self, format, *args):
        """Suppress default logging"""
        pass

    def _check_auth(self):
        """Verify authorization header"""
        auth_header = self.headers.get("Authorization", "")
        if not auth_header.startswith("Basic "):
            return False
        return True

    def _send_json(self, data, status=200):
        """Send JSON response"""
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _send_error_json(self, message, status=400):
        """Send error response"""
        self._send_json({"message": message}, status)

    def do_GET(self):
        """Handle GET requests"""
        if not self._check_auth():
            self._send_error_json("Unauthorized", 401)
            return

        path = urlparse(self.path).path

        # Get projects
        if path.endswith("/_apis/projects"):
            self._send_json({"count": len(self.projects), "value": self.projects})

        # Get specific pull request (check first before general PRs)
        elif "/pullrequests/" in path and path.count("/") > 6:
            parts = path.split("/")
            project = parts[2]
            repo = parts[6]
            pr_id = int(parts[8].split("?")[0])

            key = f"{project}/{repo}"
            prs = self.pull_requests.get(key, [])
            pr = next((p for p in prs if p["pullRequestId"] == pr_id), None)

            if pr:
                self._send_json(pr)
            else:
                self._send_error_json("Pull request not found", 404)

        # Get pull requests (list)
        elif "/pullrequests" in path and "/workitems" not in path:
            parts = path.split("/")
            project = parts[2]
            repo = parts[6]

            query = parse_qs(urlparse(self.path).query)
            status = query.get("searchCriteria.status", ["active"])[0]

            key = f"{project}/{repo}"
            all_prs = self.pull_requests.get(key, [])

            if status == "all":
                filtered_prs = all_prs
            else:
                filtered_prs = [pr for pr in all_prs if pr["status"] == status]

            self._send_json({"count": len(filtered_prs), "value": filtered_prs})

        # Get repositories
        elif "/_apis/git/repositories" in path and "/pullrequests" not in path:
            project = path.split("/")[2]
            repos = self.repositories.get(project, [])
            self._send_json({"count": len(repos), "value": repos})

        # Get specific pull request
        elif "/pullrequests/" in path and path.count("/") > 6:
            parts = path.split("/")
            print(f"DEBUG: Path parts: {parts}")
            project = parts[2]
            repo = parts[6]
            pr_id = int(parts[8].split("?")[0])
            print(f"DEBUG: project={project}, repo={repo}, pr_id={pr_id}")

            key = f"{project}/{repo}"
            prs = self.pull_requests.get(key, [])
            print(f"DEBUG: Looking for PRs with key: {key}, found: {len(prs)}")
            pr = next((p for p in prs if p["pullRequestId"] == pr_id), None)

            if pr:
                print(f"DEBUG: Found PR: {pr}")
                self._send_json(pr)
            else:
                print(f"DEBUG: PR not found for key: {key}, pr_id: {pr_id}")
                self._send_error_json("Pull request not found", 404)

        # Get work item
        elif "/workitems/" in path:
            wi_id = int(path.split("/")[-1].split("?")[0])
            wi = self.work_items.get(wi_id)

            if wi:
                self._send_json(wi)
            else:
                self._send_error_json("Work item not found", 404)

        else:
            self._send_error_json("Not found", 404)

    def do_POST(self):
        """Handle POST requests"""
        if not self._check_auth():
            self._send_error_json("Unauthorized", 401)
            return

        path = urlparse(self.path).path
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode() if content_length > 0 else "{}"
        data = json.loads(body)

        # Create project
        if path.endswith("/_apis/projects"):
            project = {
                "id": f"proj-{len(self.projects) + 1}",
                "name": data["name"],
                "description": data.get("description", ""),
                "url": f"http://localhost:8080/DefaultCollection/_apis/projects/proj-{len(self.projects) + 1}",
            }
            self.projects.append(project)
            self.repositories[data["name"]] = []
            self._send_json(project, 201)

        # Create pull request
        elif "/pullrequests" in path and "wiql" not in path and "/threads" not in path:
            parts = path.split("/")
            project = parts[2]
            repo = parts[6]

            key = f"{project}/{repo}"
            if key not in self.pull_requests:
                self.pull_requests[key] = []

            pr = {
                "pullRequestId": self.next_pr_id,
                "title": data["title"],
                "description": data.get("description", ""),
                "sourceRefName": data["sourceRefName"],
                "targetRefName": data["targetRefName"],
                "status": "active",
                "isDraft": data.get("isDraft", False),
                "createdBy": {
                    "displayName": "Test User",
                    "uniqueName": "test@example.com",
                },
                "creationDate": "2024-01-16T12:00:00Z",
                "url": f"http://localhost:8080/DefaultCollection/{project}/_git/{repo}/pullrequest/{self.next_pr_id}",
            }
            self.next_pr_id += 1
            self.pull_requests[key].append(pr)
            self._send_json(pr, 201)

        # Create pull request thread (comment)
        elif "/threads" in path:
            # Mock thread response
            thread = {
                "id": 1,
                "comments": data.get("comments", []),
                "status": data.get("status", 1),
                "publishedDate": "2024-01-16T12:00:00Z",
            }

            # Add mock comment IDs
            raw_comments = thread.get("comments", [])
            comments = (
                raw_comments
                if isinstance(raw_comments, list)
                else [raw_comments]
                if raw_comments
                else []
            )
            for i, comment in enumerate(comments):
                comment["id"] = i + 1
                comment["author"] = {
                    "displayName": "Test User",
                    "uniqueName": "test@example.com",
                }
                comment["publishedDate"] = "2024-01-16T12:00:00Z"

            self._send_json(thread, 201)

        # Query work items (WIQL)
        elif "/wiql" in path:
            project = path.split("/")[2]
            # Return mock work items for the project
            matching_wis = [
                {"id": wi_id}
                for wi_id, wi in self.work_items.items()
                if wi["fields"].get("System.TeamProject") == project
            ]
            self._send_json(
                {
                    "workItems": matching_wis[:10]  # Limit to 10
                }
            )

        else:
            self._send_error_json("Not found", 404)

    def do_PATCH(self):
        """Handle PATCH requests"""
        if not self._check_auth():
            self._send_error_json("Unauthorized", 401)
            return

        path = urlparse(self.path).path
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode() if content_length > 0 else "[]"
        data = json.loads(body)

        # Update pull request
        if "/pullrequests/" in path:
            parts = path.split("/")
            project = parts[2]
            repo = parts[6]
            pr_id = int(parts[8].split("?")[0])

            key = f"{project}/{repo}"
            prs = self.pull_requests.get(key, [])
            pr = next((p for p in prs if p["pullRequestId"] == pr_id), None)

            if pr:
                pr.update(data)
                self._send_json(pr)
            else:
                self._send_error_json("Pull request not found", 404)

        # Create work item
        elif "/workitems/" in path:
            wi_type = path.split("/")[-1].split("?")[0]

            fields = {}
            for op in data:
                if op["op"] == "add" and op["path"].startswith("/fields/"):
                    field_name = op["path"].replace("/fields/", "")
                    fields[field_name] = op["value"]

            wi = {
                "id": self.next_wi_id,
                "fields": {
                    **fields,
                    "System.WorkItemType": wi_type,
                    "System.State": "New",
                    "System.CreatedDate": "2024-01-16T12:00:00Z",
                },
                "_links": {
                    "html": {
                        "href": f"http://localhost:8080/DefaultCollection/_workitems/edit/{self.next_wi_id}"
                    }
                },
            }
            self.work_items[self.next_wi_id] = wi
            self.next_wi_id += 1
            self._send_json(wi, 201)

        else:
            self._send_error_json("Not found", 404)


class MockAzureDevOpsServer:
    """Mock Azure DevOps Server"""

    def __init__(self, port=8080):
        self.port = port
        self.server = None
        self.thread = None

    def start(self):
        """Start the mock server"""
        self.server = HTTPServer(("localhost", self.port), MockAzureDevOpsHandler)
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.daemon = True
        self.thread.start()
        time.sleep(0.5)  # Give server time to start

        # Initialize with default project
        self._setup_default_data()

    def _setup_default_data(self):
        """Setup initial test data"""
        MockAzureDevOpsHandler.next_pr_id = 2  # Start from 2 since we have PR 1
        MockAzureDevOpsHandler.next_wi_id = (
            1001  # Start from 1001 since we have WI 1000
        )
        MockAzureDevOpsHandler.projects = [
            {
                "id": "proj-1",
                "name": "TestProject",
                "description": "Test project for CLI",
                "url": "http://localhost:8080/DefaultCollection/_apis/projects/proj-1",
            }
        ]

        MockAzureDevOpsHandler.repositories = {
            "TestProject": [
                {
                    "id": "repo-1",
                    "name": "TestRepo",
                    "remoteUrl": "http://localhost:8080/DefaultCollection/TestProject/_git/TestRepo",
                    "defaultBranch": "refs/heads/main",
                }
            ]
        }

        # Add a sample PR
        MockAzureDevOpsHandler.pull_requests["TestProject/TestRepo"] = [
            {
                "pullRequestId": 1,
                "title": "Sample PR",
                "description": "This is a test pull request",
                "sourceRefName": "refs/heads/feature",
                "targetRefName": "refs/heads/main",
                "status": "active",
                "isDraft": False,
                "createdBy": {
                    "displayName": "Test User",
                    "uniqueName": "test@example.com",
                },
                "creationDate": "2024-01-16T12:00:00Z",
                "url": "http://localhost:8080/DefaultCollection/TestProject/_git/TestRepo/pullrequest/1",
            }
        ]

        # Add a sample work item
        MockAzureDevOpsHandler.work_items[1000] = {
            "id": 1000,
            "fields": {
                "System.WorkItemType": "Bug",
                "System.Title": "Sample Bug",
                "System.Description": "This is a test bug",
                "System.State": "Active",
                "System.TeamProject": "TestProject",
                "System.CreatedDate": "2024-01-16T12:00:00Z",
                "System.AssignedTo": {"displayName": "Test User"},
            },
            "_links": {
                "html": {
                    "href": "http://localhost:8080/DefaultCollection/_workitems/edit/1000"
                }
            },
        }

    def stop(self):
        """Stop the mock server"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            if self.thread:
                self.thread.join(timeout=1)


if __name__ == "__main__":
    # Run mock server for manual testing
    server = MockAzureDevOpsServer(port=8080)
    server.start()
    print("Mock Azure DevOps Server running on http://localhost:8080")
    print("Press Ctrl+C to stop")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping server...")
        server.stop()
