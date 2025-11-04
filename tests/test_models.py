"""Test cases for the Snippet model"""

from datetime import datetime, timezone

import pytest

from pypet.models import Parameter, Snippet


def test_snippet_creation():
    """Test basic snippet creation"""
    snippet = Snippet(command="ls -la")
    assert snippet.command == "ls -la"
    assert snippet.description is None
    assert snippet.tags == []
    assert isinstance(snippet.created_at, datetime)
    assert isinstance(snippet.updated_at, datetime)


def test_snippet_with_metadata():
    """Test snippet creation with all metadata"""
    now = datetime.now(timezone.utc)
    snippet = Snippet(
        command="git commit -m",
        description="Create a git commit",
        tags=["git", "version-control"],
        created_at=now,
        updated_at=now,
    )

    assert snippet.command == "git commit -m"
    assert snippet.description == "Create a git commit"
    assert snippet.tags == ["git", "version-control"]
    assert snippet.created_at == now
    assert snippet.updated_at == now


def test_snippet_to_dict():
    """Test conversion of snippet to dictionary"""
    snippet = Snippet(
        command="git status", description="Check git status", tags=["git", "status"]
    )

    data = snippet.to_dict()
    assert data["command"] == "git status"
    assert data["description"] == "Check git status"
    assert data["tags"] == ["git", "status"]
    assert isinstance(data["created_at"], str)
    assert isinstance(data["updated_at"], str)


def test_snippet_from_dict():
    """Test creation of snippet from dictionary"""
    now = datetime.now(timezone.utc)
    data = {
        "command": "docker ps",
        "description": "List containers",
        "tags": ["docker", "container"],
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }

    snippet = Snippet.from_dict(data)
    assert snippet.command == "docker ps"
    assert snippet.description == "List containers"
    assert snippet.tags == ["docker", "container"]
    assert snippet.created_at.isoformat() == now.isoformat()
    assert snippet.updated_at.isoformat() == now.isoformat()


def test_empty_snippet():
    """Test creating a snippet with empty values"""
    snippet = Snippet(command="")
    assert snippet.command == ""
    assert snippet.description is None
    assert snippet.tags == []


def test_snippet_normalization():
    """Test normalization of snippet fields"""
    snippet = Snippet(
        command="  git status  ",
        description="  Check status  ",
        tags=[
            " tag1 ",
            "tag2  ",
            "  tag3",
            "",
            "  ",
            " tag1 ",
        ],  # Duplicates and empty tags
    )

    assert snippet.command == "git status"  # Should strip whitespace
    assert snippet.description == "Check status"  # Should strip whitespace
    assert snippet.tags == [
        "tag1",
        "tag2",
        "tag3",
    ]  # Should clean tags and remove duplicates


def test_snippet_from_dict_invalid_date():
    """Test snippet creation with invalid date string"""
    data = {
        "command": "test",
        "created_at": "invalid-date",
        "updated_at": "invalid-date",
    }

    with pytest.raises(ValueError):
        Snippet.from_dict(data)


def test_snippet_from_dict_missing_dates():
    """Test snippet creation with missing date fields"""
    data = {"command": "test"}

    snippet = Snippet.from_dict(data)
    assert isinstance(snippet.created_at, datetime)
    assert isinstance(snippet.updated_at, datetime)


def test_snippet_empty_tags():
    """Test snippet creation with empty tag input"""
    snippet = Snippet(command="test", tags=[])
    assert snippet.tags == []  # Should be an empty list

    snippet = Snippet(command="test", tags=None)
    assert snippet.tags == []  # Should initialize to empty list


# Parameter Tests


def test_parameter_creation():
    """Test basic parameter creation"""
    param = Parameter(name="host")
    assert param.name == "host"
    assert param.default is None
    assert param.description is None


def test_parameter_with_default():
    """Test parameter creation with default value"""
    param = Parameter(name="port", default="8080")
    assert param.name == "port"
    assert param.default == "8080"
    assert param.description is None


def test_parameter_with_description():
    """Test parameter creation with description"""
    param = Parameter(name="user", description="Username for connection")
    assert param.name == "user"
    assert param.default is None
    assert param.description == "Username for connection"


def test_parameter_with_all_fields():
    """Test parameter creation with all fields"""
    param = Parameter(
        name="timeout", default="30", description="Connection timeout in seconds"
    )
    assert param.name == "timeout"
    assert param.default == "30"
    assert param.description == "Connection timeout in seconds"


def test_parameter_normalization():
    """Test parameter field normalization"""
    param = Parameter(name="  host  ", description="  Server host  ")
    assert param.name == "host"
    assert param.description == "Server host"


def test_parameter_to_dict():
    """Test parameter to dictionary conversion"""
    param = Parameter(name="port", default="8080", description="Server port")
    data = param.to_dict()
    assert data == {"name": "port", "default": "8080", "description": "Server port"}


def test_parameter_from_dict():
    """Test parameter from dictionary creation"""
    data = {"name": "host", "default": "localhost", "description": "Server hostname"}
    param = Parameter.from_dict(data)
    assert param.name == "host"
    assert param.default == "localhost"
    assert param.description == "Server hostname"


# Snippet with Parameters Tests


def test_snippet_with_formal_parameters():
    """Test snippet creation with formal parameters"""
    params = {
        "host": Parameter("host", description="Server host"),
        "port": Parameter("port", default="22", description="SSH port"),
    }
    snippet = Snippet(
        command="ssh {user}@{host} -p {port}",
        description="SSH connection",
        parameters=params,
    )

    assert snippet.command == "ssh {user}@{host} -p {port}"
    assert len(snippet.parameters) == 2
    assert "host" in snippet.parameters
    assert "port" in snippet.parameters


def test_get_all_parameters_with_formal_only():
    """Test get_all_parameters with only formally defined parameters"""
    params = {
        "host": Parameter("host", description="Server host"),
        "port": Parameter("port", default="22"),
    }
    snippet = Snippet(command="ssh user@{host} -p {port}", parameters=params)

    all_params = snippet.get_all_parameters()
    assert len(all_params) == 2
    assert "host" in all_params
    assert "port" in all_params
    assert all_params["host"].description == "Server host"
    assert all_params["port"].default == "22"


def test_get_all_parameters_discover_from_command():
    """Test get_all_parameters discovering parameters from command string"""
    snippet = Snippet(command="ssh {user}@{host} -p {port=22}")

    all_params = snippet.get_all_parameters()
    assert len(all_params) == 3
    assert "user" in all_params
    assert "host" in all_params
    assert "port" in all_params

    # Check discovered parameters
    assert all_params["user"].default is None
    assert all_params["host"].default is None
    assert all_params["port"].default == "22"

    # All discovered parameters should have no description
    assert all_params["user"].description is None
    assert all_params["host"].description is None
    assert all_params["port"].description is None


def test_get_all_parameters_mixed():
    """Test get_all_parameters with both formal and discovered parameters"""
    # Formal parameter definitions
    formal_params = {
        "host": Parameter("host", description="Server hostname"),
        "timeout": Parameter("timeout", default="30", description="Connection timeout"),
    }

    # Command has both formal and additional parameters
    snippet = Snippet(
        command="ssh {user}@{host} -p {port=22} -o ConnectTimeout={timeout}",
        parameters=formal_params,
    )

    all_params = snippet.get_all_parameters()
    assert len(all_params) == 4  # host, timeout (formal) + user, port (discovered)

    # Check formal parameters (should keep their definitions)
    assert all_params["host"].description == "Server hostname"
    assert all_params["timeout"].default == "30"
    assert all_params["timeout"].description == "Connection timeout"

    # Check discovered parameters
    assert all_params["user"].default is None
    assert all_params["user"].description is None
    assert all_params["port"].default == "22"
    assert all_params["port"].description is None


def test_apply_parameters_no_params():
    """Test apply_parameters on snippet without parameters"""
    snippet = Snippet(command="docker ps")
    result = snippet.apply_parameters({})
    assert result == "docker ps"


def test_apply_parameters_formal_params():
    """Test apply_parameters with formally defined parameters"""
    params = {
        "host": Parameter("host", description="Server host"),
        "port": Parameter("port", default="22"),
    }
    snippet = Snippet(command="ssh user@{host} -p {port}", parameters=params)

    # With all parameters provided
    result = snippet.apply_parameters({"host": "example.com", "port": "2222"})
    assert result == "ssh user@example.com -p 2222"

    # With only required parameter (should use default for port)
    result = snippet.apply_parameters({"host": "example.com"})
    assert result == "ssh user@example.com -p 22"


def test_apply_parameters_discovered_params():
    """Test apply_parameters with discovered parameters from command"""
    snippet = Snippet(command="ssh {user}@{host} -p {port=22}")

    # With all parameters provided
    result = snippet.apply_parameters(
        {"user": "admin", "host": "example.com", "port": "2222"}
    )
    assert result == "ssh admin@example.com -p 2222"

    # With only required parameters (should use default for port)
    result = snippet.apply_parameters({"user": "admin", "host": "example.com"})
    assert result == "ssh admin@example.com -p 22"


def test_apply_parameters_missing_required():
    """Test apply_parameters with missing required parameters"""
    snippet = Snippet(command="ssh {user}@{host} -p {port=22}")

    # Missing required parameter should raise ValueError
    with pytest.raises(
        ValueError, match="No value provided for required parameter: host"
    ):
        snippet.apply_parameters({"user": "admin"})

    with pytest.raises(
        ValueError, match="No value provided for required parameter: user"
    ):
        snippet.apply_parameters({"host": "example.com"})


def test_apply_parameters_complex_patterns():
    """Test apply_parameters with various parameter patterns"""
    snippet = Snippet(command="echo Hello {name} from {location=world} on port {port}")

    result = snippet.apply_parameters(
        {"name": "Alice", "location": "Mars", "port": "8080"}
    )
    assert result == "echo Hello Alice from Mars on port 8080"

    # Test with default used
    result = snippet.apply_parameters({"name": "Bob", "port": "9090"})
    assert result == "echo Hello Bob from world on port 9090"


def test_apply_parameters_dollar_syntax():
    """Test apply_parameters with ${var} syntax"""
    snippet = Snippet(command="echo ${message} to {user}")

    result = snippet.apply_parameters({"message": "Hello", "user": "World"})
    assert result == "echo Hello to World"


def test_apply_parameters_edge_cases():
    """Test apply_parameters with edge cases"""
    # Empty braces should be ignored
    snippet = Snippet(command="echo {} and {valid}")
    result = snippet.apply_parameters({"valid": "test"})
    assert result == "echo {} and test"

    # Nested braces (should only process outer)
    snippet = Snippet(command="echo {outer{inner}}")
    # This should discover parameter "outer{inner"
    all_params = snippet.get_all_parameters()
    assert "outer{inner" in all_params

    # Malformed parameters should be handled gracefully
    snippet = Snippet(command="echo {missing_closing")
    all_params = snippet.get_all_parameters()
    assert len(all_params) == 0  # No valid parameters found
