"""Test cases for the Storage system"""

import sys

import pytest
import toml

from pypet.models import Parameter
from pypet.storage import Storage


@pytest.fixture
def temp_storage(tmp_path):
    """Create a temporary storage for testing"""
    storage_path = tmp_path / "test_snippets.toml"
    return Storage(config_path=storage_path)


def test_storage_initialization(temp_storage, tmp_path):
    """Test storage initialization"""
    expected_path = tmp_path / "test_snippets.toml"
    assert temp_storage.config_path == expected_path
    assert temp_storage.config_path.exists()


def test_add_and_get_snippet(temp_storage):
    """Test adding and retrieving a snippet"""
    # Add a new snippet
    snippet_id = temp_storage.add_snippet(
        command="echo 'hello'", description="Print hello", tags=["test", "echo"]
    )

    # Verify it was added
    assert snippet_id is not None

    # Retrieve and verify
    snippet = temp_storage.get_snippet(snippet_id)
    assert snippet is not None
    assert snippet.command == "echo 'hello'"
    assert snippet.description == "Print hello"
    assert snippet.tags == ["test", "echo"]


def test_list_snippets(temp_storage):
    """Test listing all snippets"""
    # Add some test snippets
    id1 = temp_storage.add_snippet("cmd1", "desc1", ["tag1"])
    id2 = temp_storage.add_snippet("cmd2", "desc2", ["tag2"])

    # List all snippets
    snippets = temp_storage.list_snippets()
    assert len(snippets) == 2

    # Convert to dict for easier comparison
    snippet_dict = dict(snippets)

    assert snippet_dict[id1].command == "cmd1"
    assert snippet_dict[id2].command == "cmd2"


def test_search_snippets(temp_storage):
    """Test searching snippets"""
    # Add test snippets
    temp_storage.add_snippet(
        "git commit", "Create a commit", ["git", "version-control"]
    )
    temp_storage.add_snippet("git push", "Push changes", ["git", "remote"])
    temp_storage.add_snippet("docker ps", "List containers", ["docker"])

    # Search by command
    git_results = temp_storage.search_snippets("git")
    assert len(git_results) == 2

    # Search by description
    container_results = temp_storage.search_snippets("container")
    assert len(container_results) == 1

    # Search by tag
    remote_results = temp_storage.search_snippets("remote")
    assert len(remote_results) == 1


def test_search_snippets_by_alias(temp_storage):
    """Test searching snippets by alias name"""
    # Add test snippets with aliases
    temp_storage.add_snippet(
        "git status", "Show git status", ["git"], alias="gst"
    )
    temp_storage.add_snippet(
        "docker ps -a", "List all containers", ["docker"], alias="dps"
    )
    temp_storage.add_snippet(
        "kubectl get pods", "List kubernetes pods", ["k8s"]
    )  # No alias

    # Search by alias
    gst_results = temp_storage.search_snippets("gst")
    assert len(gst_results) == 1
    assert gst_results[0][1].alias == "gst"

    # Search by partial alias
    dps_results = temp_storage.search_snippets("dps")
    assert len(dps_results) == 1
    assert dps_results[0][1].command == "docker ps -a"

    # Search for snippet without alias should still work by command
    k8s_results = temp_storage.search_snippets("kubectl")
    assert len(k8s_results) == 1


def test_update_snippet(temp_storage):
    """Test updating a snippet"""
    # Add a snippet
    snippet_id = temp_storage.add_snippet("initial command", "initial desc", ["tag1"])

    # Update it
    success = temp_storage.update_snippet(
        snippet_id, command="updated command", description="updated desc", tags=["tag2"]
    )
    assert success

    # Verify updates
    updated = temp_storage.get_snippet(snippet_id)
    assert updated.command == "updated command"
    assert updated.description == "updated desc"
    assert updated.tags == ["tag2"]


def test_delete_snippet(temp_storage):
    """Test deleting a snippet"""
    # Add a snippet
    snippet_id = temp_storage.add_snippet("test command")

    # Verify it exists
    assert temp_storage.get_snippet(snippet_id) is not None

    # Delete it
    success = temp_storage.delete_snippet(snippet_id)
    assert success

    # Verify it's gone
    assert temp_storage.get_snippet(snippet_id) is None


def test_invalid_snippet_operations(temp_storage):
    """Test operations with invalid snippet IDs"""
    invalid_id = "nonexistent"

    # Try to get nonexistent snippet
    assert temp_storage.get_snippet(invalid_id) is None

    # Try to update nonexistent snippet
    assert not temp_storage.update_snippet(invalid_id, command="test")

    # Try to delete nonexistent snippet
    assert not temp_storage.delete_snippet(invalid_id)


def test_search_case_sensitivity(temp_storage):
    """Test case sensitivity in search"""
    temp_storage.add_snippet("GIT status", "Check Status", ["Git"])
    temp_storage.add_snippet("docker PS", "List Containers", ["Docker"])

    # Case-insensitive search (default)
    assert len(temp_storage.search_snippets("git")) == 1
    assert len(temp_storage.search_snippets("docker")) == 1
    assert (
        len(temp_storage.search_snippets("STATUS")) == 1
    )  # Matches only first description


def test_search_special_characters(temp_storage):
    """Test searching with special characters"""
    temp_storage.add_snippet("grep -r 'pattern'", "Search with quotes", ["grep"])
    temp_storage.add_snippet("echo $PATH", "Print path", ["shell"])
    temp_storage.add_snippet("ls && pwd", "Multiple commands", ["shell"])

    assert len(temp_storage.search_snippets("'pattern'")) == 1
    assert len(temp_storage.search_snippets("$PATH")) == 1
    assert len(temp_storage.search_snippets("&&")) == 1


def test_invalid_snippet_id(temp_storage):
    """Test operations with invalid snippet IDs"""
    invalid_id = "non-existent-id"

    assert temp_storage.get_snippet(invalid_id) is None
    assert not temp_storage.update_snippet(invalid_id, command="new")
    assert not temp_storage.delete_snippet(invalid_id)


def test_duplicate_snippets(temp_storage):
    """Test adding duplicate snippets"""
    cmd = "echo 'test'"
    desc = "Test command"
    tags = ["test"]

    id1 = temp_storage.add_snippet(cmd, desc, tags)
    id2 = temp_storage.add_snippet(cmd, desc, tags)

    assert id1 != id2  # Should generate unique IDs
    snippets = temp_storage.list_snippets()
    assert len(snippets) == 2  # Both snippets should be stored


@pytest.mark.skipif(
    sys.platform == "win32", reason="File permissions work differently on Windows"
)
def test_file_permission_error(tmp_path):
    """Test handling of file permission errors"""
    storage_path = tmp_path / "test_snippets.toml"
    storage_path.touch()
    storage_path.chmod(0o000)  # Remove all permissions

    storage = Storage(config_path=storage_path)
    with pytest.raises(PermissionError):
        storage.add_snippet("test", "test")


def test_no_empty_parameters_in_toml(temp_storage):
    """Test that snippets without parameters don't have empty parameters section in TOML"""
    # Add a snippet without parameters
    snippet_id = temp_storage.add_snippet(
        command="git status", description="Check git status", tags=["git"]
    )

    # Load the TOML file directly and check the structure
    with temp_storage.config_path.open("r") as f:
        toml_data = toml.load(f)

    # Verify the snippet exists
    assert snippet_id in toml_data

    # Verify that parameters key is not present at all
    assert "parameters" not in toml_data[snippet_id]

    # Verify that other fields are present
    assert toml_data[snippet_id]["command"] == "git status"
    assert toml_data[snippet_id]["description"] == "Check git status"
    assert toml_data[snippet_id]["tags"] == ["git"]


def test_parameters_in_toml_when_present(temp_storage):
    """Test that snippets with parameters DO have parameters section in TOML"""
    # Add a snippet with parameters
    params = {
        "host": Parameter("host", description="Server host"),
        "port": Parameter("port", default="22", description="SSH port"),
    }
    snippet_id = temp_storage.add_snippet(
        command="ssh user@{host} -p {port}",
        description="SSH connection",
        tags=["ssh"],
        parameters=params,
    )

    # Load the TOML file directly and check the structure
    with temp_storage.config_path.open("r") as f:
        toml_data = toml.load(f)

    # Verify the snippet exists
    assert snippet_id in toml_data

    # Verify that parameters key IS present and has the correct structure
    assert "parameters" in toml_data[snippet_id]
    assert "host" in toml_data[snippet_id]["parameters"]
    assert "port" in toml_data[snippet_id]["parameters"]

    # Verify parameter details
    assert toml_data[snippet_id]["parameters"]["host"]["name"] == "host"
    assert toml_data[snippet_id]["parameters"]["host"]["description"] == "Server host"
    assert toml_data[snippet_id]["parameters"]["port"]["default"] == "22"
