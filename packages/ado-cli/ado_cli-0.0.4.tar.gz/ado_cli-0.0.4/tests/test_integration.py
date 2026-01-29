import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mock_server import MockAzureDevOpsServer
from ado.client import AdoClient
from ado.config import AdoConfig
import ado.config as config_module


def test_with_mock_server():
    """Test CLI against mock Azure DevOps Server"""

    # Start mock server
    print("Starting mock server...")
    server = MockAzureDevOpsServer(port=8080)
    server.start()

    # Create temp config
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / "config.json"
        original_file = config_module.CONFIG_FILE
        config_module.CONFIG_FILE = str(config_file)

        try:
            # Test client
            print("Testing client...")
            client = AdoClient(
                server_url="http://localhost:8080",
                pat="test-pat",
                collection="DefaultCollection",
            )

            # Test get projects
            projects = client.get_projects()
            assert len(projects["value"]) == 1
            assert projects["value"][0]["name"] == "TestProject"
            print("✓ Get projects works")

            # Test get repos
            repos = client.get_repos("TestProject")
            assert len(repos["value"]) == 1
            assert repos["value"][0]["name"] == "TestRepo"
            print("✓ Get repos works")

            # Test get pull requests
            prs = client.get_pull_requests("TestProject", "TestRepo")
            assert len(prs["value"]) == 1
            assert prs["value"][0]["title"] == "Sample PR"
            print("✓ Get pull requests works")

            # Test get specific PR
            pr = client.get_pull_request("TestProject", "TestRepo", 1)
            assert pr["pullRequestId"] == 1
            print("✓ Get specific PR works")

            # Test create pull request
            new_pr = client.create_pull_request(
                "TestProject",
                "TestRepo",
                {
                    "title": "New PR",
                    "description": "Test description",
                    "sourceRefName": "refs/heads/feature",
                    "targetRefName": "refs/heads/main",
                },
            )
            assert new_pr["pullRequestId"] == 2
            assert new_pr["title"] == "New PR"
            print("✓ Create PR works")

            # Test update pull request
            updated = client.update_pull_request(
                "TestProject", "TestRepo", 1, {"status": "abandoned"}
            )
            assert updated["status"] == "abandoned"
            print("✓ Update PR works")

            # Test get work item
            wi = client.get_work_item(1000)
            assert wi["id"] == 1000
            assert wi["fields"]["System.Title"] == "Sample Bug"
            print("✓ Get work item works")

            # Test create work item
            new_wi = client.create_work_item(
                "TestProject",
                "Bug",
                [
                    {"op": "add", "path": "/fields/System.Title", "value": "New Bug"},
                    {
                        "op": "add",
                        "path": "/fields/System.Description",
                        "value": "Test bug",
                    },
                ],
            )
            assert new_wi["fields"]["System.Title"] == "New Bug"
            print("✓ Create work item works")

            # Test create pull request thread (comment)
            thread_data = {
                "comments": [
                    {
                        "parentCommentId": 0,
                        "content": "This looks good!",
                        "commentType": 1,
                    }
                ],
                "status": 1,
            }
            result = client.create_pull_request_thread(
                "TestProject", "TestRepo", 1, thread_data
            )
            assert result["id"] is not None
            assert result["comments"][0]["content"] == "This looks good!"
            print("✓ Create PR thread works")

            # Test config
            print("Testing config...")
            cfg = AdoConfig()
            cfg.set("server_url", "http://localhost:8080")
            cfg.set("pat", "test-pat")
            cfg.set("collection", "DefaultCollection")

            assert cfg.get("server_url") == "http://localhost:8080"
            print("✓ Config works")

            print("\n✅ All integration tests passed!")

        finally:
            config_module.CONFIG_FILE = original_file
            server.stop()


if __name__ == "__main__":
    test_with_mock_server()
