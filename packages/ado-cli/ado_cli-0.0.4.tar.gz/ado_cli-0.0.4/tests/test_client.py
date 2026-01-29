import sys
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_client_initialization():
    """Test client can be initialized"""
    from ado.client import AdoClient

    client = AdoClient(
        server_url="https://test-server.com",
        pat="test-pat",
        collection="TestCollection",
    )

    assert client.server_url == "https://test-server.com"
    assert client.collection == "TestCollection"
    assert client.base_url == "https://test-server.com/TestCollection"
    assert "Authorization" in client.headers

    print("✓ Client initialization test passed")


def test_pat_encoding():
    """Test PAT encoding for basic auth"""
    from ado.client import AdoClient
    import base64

    client = AdoClient(
        server_url="https://test.com", pat="test-pat-123", collection="Default"
    )

    # Verify the PAT is properly base64 encoded
    auth_header = client.headers["Authorization"]
    assert auth_header.startswith("Basic ")

    encoded_pat = auth_header.replace("Basic ", "")
    decoded = base64.b64decode(encoded_pat).decode()
    assert decoded == ":test-pat-123"

    print("✓ PAT encoding test passed")


if __name__ == "__main__":
    test_client_initialization()
    test_pat_encoding()
