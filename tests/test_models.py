"""Test cases for the Snippet model"""

from datetime import datetime, timezone
import pytest
from pypet.models import Snippet


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
