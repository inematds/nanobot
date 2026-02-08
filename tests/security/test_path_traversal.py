"""Tests for path traversal prevention in filesystem tools."""

import pytest

from nanobot.agent.tools.filesystem import ReadFileTool, WriteFileTool, EditFileTool, ListDirTool


@pytest.fixture
def workspace(tmp_path):
    """Create a test workspace directory."""
    ws = tmp_path / "workspace"
    ws.mkdir()
    (ws / "test.txt").write_text("hello")
    (ws / "subdir").mkdir()
    (ws / "subdir" / "nested.txt").write_text("nested content")
    return ws


class TestReadFileTraversal:
    """Test path traversal prevention in ReadFileTool."""

    @pytest.mark.asyncio
    async def test_read_within_workspace(self, workspace):
        tool = ReadFileTool(allowed_dir=workspace)
        result = await tool.execute(str(workspace / "test.txt"))
        assert result == "hello"

    @pytest.mark.asyncio
    async def test_read_nested(self, workspace):
        tool = ReadFileTool(allowed_dir=workspace)
        result = await tool.execute(str(workspace / "subdir" / "nested.txt"))
        assert result == "nested content"

    @pytest.mark.asyncio
    async def test_read_traversal_blocked(self, workspace):
        tool = ReadFileTool(allowed_dir=workspace)
        result = await tool.execute(str(workspace / ".." / "outside.txt"))
        assert "error" in result.lower()

    @pytest.mark.asyncio
    async def test_read_absolute_outside_blocked(self, workspace):
        tool = ReadFileTool(allowed_dir=workspace)
        result = await tool.execute("/etc/passwd")
        assert "error" in result.lower()

    @pytest.mark.asyncio
    async def test_read_file_too_large(self, workspace):
        big_file = workspace / "big.txt"
        big_file.write_bytes(b"x" * (11 * 1024 * 1024))  # 11MB
        tool = ReadFileTool(allowed_dir=workspace)
        result = await tool.execute(str(big_file))
        assert "too large" in result.lower()


class TestWriteFileTraversal:
    """Test path traversal prevention in WriteFileTool."""

    @pytest.mark.asyncio
    async def test_write_within_workspace(self, workspace):
        tool = WriteFileTool(allowed_dir=workspace)
        result = await tool.execute(str(workspace / "new.txt"), "new content")
        assert "successfully" in result.lower()

    @pytest.mark.asyncio
    async def test_write_traversal_blocked(self, workspace):
        tool = WriteFileTool(allowed_dir=workspace)
        result = await tool.execute(str(workspace / ".." / "escape.txt"), "bad")
        assert "error" in result.lower()

    @pytest.mark.asyncio
    async def test_write_content_too_large(self, workspace):
        tool = WriteFileTool(allowed_dir=workspace)
        big_content = "x" * (11 * 1024 * 1024)  # 11MB
        result = await tool.execute(str(workspace / "big.txt"), big_content)
        assert "too large" in result.lower()


class TestListDirTraversal:
    """Test path traversal prevention in ListDirTool."""

    @pytest.mark.asyncio
    async def test_list_workspace(self, workspace):
        tool = ListDirTool(allowed_dir=workspace)
        result = await tool.execute(str(workspace))
        assert "test.txt" in result

    @pytest.mark.asyncio
    async def test_list_outside_blocked(self, workspace):
        tool = ListDirTool(allowed_dir=workspace)
        result = await tool.execute("/tmp")
        assert "error" in result.lower()
