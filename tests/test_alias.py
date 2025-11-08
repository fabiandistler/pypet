"""Test cases for alias functionality"""

import tempfile
from pathlib import Path

import pytest

from pypet.alias_manager import AliasManager
from pypet.models import Parameter, Snippet
from pypet.storage import Storage


@pytest.fixture
def temp_alias_path():
    """Create a temporary alias file path"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "aliases.sh"


@pytest.fixture
def temp_storage():
    """Create a temporary storage instance"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "snippets.toml"
        yield Storage(config_path)


def test_alias_manager_initialization(temp_alias_path):
    """Test alias manager initialization"""
    manager = AliasManager(temp_alias_path)
    assert manager.alias_path == temp_alias_path
    assert manager.alias_path.parent.exists()


def test_generate_alias_definition_simple(temp_alias_path):
    """Test alias generation for snippet without parameters"""
    manager = AliasManager(temp_alias_path)
    snippet = Snippet(command="ls -la", description="List all files")

    alias_def = manager._generate_alias_definition("ll", "123", snippet)
    assert alias_def == "alias ll='ls -la'"


def test_generate_alias_definition_with_parameters(temp_alias_path):
    """Test alias generation for snippet with parameters"""
    manager = AliasManager(temp_alias_path)
    snippet = Snippet(
        command="ssh {user}@{host}",
        parameters={
            "user": Parameter(name="user", default="admin"),
            "host": Parameter(name="host"),
        },
    )

    alias_def = manager._generate_alias_definition("myssh", "123", snippet)
    assert "myssh()" in alias_def
    assert "pypet exec 123" in alias_def


def test_update_aliases_file_empty(temp_alias_path):
    """Test updating aliases file with no aliases"""
    manager = AliasManager(temp_alias_path)
    manager.update_aliases_file([])

    assert temp_alias_path.exists()
    content = temp_alias_path.read_text()
    assert "pypet aliases" in content
    assert "source" in content


def test_update_aliases_file_with_snippets(temp_alias_path):
    """Test updating aliases file with snippets"""
    manager = AliasManager(temp_alias_path)

    snippets = [
        (
            "123",
            Snippet(command="ls -la", description="List all files", alias="ll"),
        ),
        (
            "456",
            Snippet(command="git status", description="Check git status", alias="gs"),
        ),
    ]

    manager.update_aliases_file(snippets)

    assert temp_alias_path.exists()
    content = temp_alias_path.read_text()
    assert "alias ll='ls -la'" in content
    assert "alias gs='git status'" in content
    assert "# List all files" in content
    assert "# Check git status" in content


def test_update_aliases_file_with_parameters(temp_alias_path):
    """Test updating aliases file with parameterized snippets"""
    manager = AliasManager(temp_alias_path)

    snippets = [
        (
            "123",
            Snippet(
                command="ssh {user}@{host}",
                description="SSH to server",
                alias="myssh",
                parameters={
                    "user": Parameter(name="user"),
                    "host": Parameter(name="host"),
                },
            ),
        ),
    ]

    manager.update_aliases_file(snippets)

    content = temp_alias_path.read_text()
    assert "myssh()" in content
    assert "pypet exec 123" in content


def test_get_source_instruction(temp_alias_path):
    """Test getting source instruction"""
    manager = AliasManager(temp_alias_path)
    instruction = manager.get_source_instruction()
    assert "source" in instruction
    assert str(temp_alias_path) in instruction


def test_get_setup_instructions(temp_alias_path):
    """Test getting setup instructions"""
    manager = AliasManager(temp_alias_path)
    instructions = manager.get_setup_instructions()
    assert len(instructions) > 0
    assert any("bashrc" in line.lower() for line in instructions)
    assert any("zshrc" in line.lower() for line in instructions)


def test_storage_add_snippet_with_alias(temp_storage):
    """Test adding snippet with alias"""
    snippet_id = temp_storage.add_snippet(
        command="ls -la", description="List files", alias="ll"
    )

    snippet = temp_storage.get_snippet(snippet_id)
    assert snippet is not None
    assert snippet.alias == "ll"


def test_storage_update_snippet_alias(temp_storage):
    """Test updating snippet alias"""
    snippet_id = temp_storage.add_snippet(command="ls -la")

    # Add alias
    success = temp_storage.update_snippet(snippet_id, alias="ll")
    assert success

    snippet = temp_storage.get_snippet(snippet_id)
    assert snippet.alias == "ll"

    # Update alias
    success = temp_storage.update_snippet(snippet_id, alias="mylist")
    assert success

    snippet = temp_storage.get_snippet(snippet_id)
    assert snippet.alias == "mylist"


def test_storage_get_snippets_with_aliases(temp_storage):
    """Test getting only snippets with aliases"""
    # Add snippets with and without aliases
    temp_storage.add_snippet(command="ls -la", alias="ll")
    temp_storage.add_snippet(command="pwd")
    temp_storage.add_snippet(command="git status", alias="gs")

    snippets_with_aliases = temp_storage.get_snippets_with_aliases()
    assert len(snippets_with_aliases) == 2

    aliases = [s.alias for _, s in snippets_with_aliases]
    assert "ll" in aliases
    assert "gs" in aliases


def test_snippet_model_with_alias():
    """Test snippet model with alias field"""
    snippet = Snippet(command="ls -la", alias="ll")
    assert snippet.alias == "ll"

    # Test to_dict
    data = snippet.to_dict()
    assert data["alias"] == "ll"

    # Test from_dict
    snippet2 = Snippet.from_dict(data)
    assert snippet2.alias == "ll"


def test_snippet_model_alias_normalization():
    """Test alias whitespace normalization"""
    snippet = Snippet(command="ls -la", alias="  ll  ")
    assert snippet.alias == "ll"


def test_snippet_model_without_alias():
    """Test snippet without alias"""
    snippet = Snippet(command="ls -la")
    assert snippet.alias is None

    data = snippet.to_dict()
    assert data["alias"] is None


def test_alias_with_special_characters(temp_alias_path):
    """Test alias generation with special shell characters"""
    manager = AliasManager(temp_alias_path)
    snippet = Snippet(command="echo 'hello world'", alias="greet")

    alias_def = manager._generate_alias_definition("greet", "123", snippet)
    assert "alias greet=" in alias_def
    assert "'" in alias_def or '"' in alias_def


def test_validate_alias_name_valid():
    """Test alias name validation with valid names"""
    manager = AliasManager()

    valid, msg = manager.validate_alias_name("my_alias")
    assert valid is True
    assert msg == ""

    valid, msg = manager.validate_alias_name("my-alias")
    assert valid is True

    valid, msg = manager.validate_alias_name("myalias123")
    assert valid is True


def test_validate_alias_name_invalid():
    """Test alias name validation with invalid names"""
    manager = AliasManager()

    valid, msg = manager.validate_alias_name("")
    assert valid is False
    assert "empty" in msg.lower()

    valid, msg = manager.validate_alias_name("my alias")
    assert valid is False
    assert "Invalid" in msg

    valid, msg = manager.validate_alias_name("my@alias")
    assert valid is False

    valid, msg = manager.validate_alias_name("a" * 65)
    assert valid is False
    assert "too long" in msg.lower()


def test_validate_snippet_id_valid(temp_alias_path):
    """Test snippet ID validation with valid IDs"""
    manager = AliasManager(temp_alias_path)

    manager.validate_snippet_id("20231201120000123456")
    manager.validate_snippet_id("abc-123")
    manager.validate_snippet_id("test_snippet_123")


def test_validate_snippet_id_invalid(temp_alias_path):
    """Test snippet ID validation rejects shell metacharacters"""
    manager = AliasManager(temp_alias_path)
    snippet = Snippet(command="echo {msg}", parameters={"msg": Parameter(name="msg")})

    with pytest.raises(ValueError, match="Invalid snippet ID"):
        manager._generate_alias_definition("test", "abc; rm -rf /", snippet)

    with pytest.raises(ValueError, match="Invalid snippet ID"):
        manager._generate_alias_definition("test", "id$(whoami)", snippet)

    with pytest.raises(ValueError, match="Invalid snippet ID"):
        manager._generate_alias_definition("test", "id`ls`", snippet)

    with pytest.raises(ValueError, match="Invalid snippet ID"):
        manager._generate_alias_definition("test", "id|cat", snippet)


def test_atomic_file_write(temp_alias_path):
    """Test that alias file is written atomically"""
    manager = AliasManager(temp_alias_path)
    snippet = Snippet(command="ls -la", alias="ll")
    snippets = [("123", snippet)]

    manager.update_aliases_file(snippets)

    assert temp_alias_path.exists()
    assert not temp_alias_path.with_suffix(".tmp").exists()

    content = temp_alias_path.read_text()
    assert content.endswith("\n")
    assert "alias ll='ls -la'" in content
