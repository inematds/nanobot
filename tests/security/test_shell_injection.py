"""Tests for shell injection prevention in ExecTool."""

import pytest
import asyncio

from nanobot.agent.tools.shell import ExecTool


@pytest.fixture
def tool():
    return ExecTool(timeout=5, restrict_to_workspace=False)


@pytest.fixture
def restricted_tool(tmp_path):
    return ExecTool(timeout=5, working_dir=str(tmp_path), restrict_to_workspace=True)


class TestShellInjectionBlocking:
    """Test that shell injection patterns are blocked."""

    @pytest.mark.asyncio
    async def test_semicolon_blocked(self, tool):
        result = await tool.execute("ls; rm -rf /")
        assert "injection" in result.lower() or "blocked" in result.lower()

    @pytest.mark.asyncio
    async def test_and_chaining_blocked(self, tool):
        result = await tool.execute("echo hello && cat /etc/passwd")
        assert "injection" in result.lower() or "blocked" in result.lower()

    @pytest.mark.asyncio
    async def test_or_chaining_blocked(self, tool):
        result = await tool.execute("false || cat /etc/passwd")
        assert "injection" in result.lower() or "blocked" in result.lower()

    @pytest.mark.asyncio
    async def test_pipe_blocked(self, tool):
        result = await tool.execute("cat /etc/passwd | head")
        assert "injection" in result.lower() or "blocked" in result.lower()

    @pytest.mark.asyncio
    async def test_backtick_blocked(self, tool):
        result = await tool.execute("echo `whoami`")
        assert "injection" in result.lower() or "blocked" in result.lower()

    @pytest.mark.asyncio
    async def test_dollar_paren_blocked(self, tool):
        result = await tool.execute("echo $(whoami)")
        assert "injection" in result.lower() or "blocked" in result.lower()

    @pytest.mark.asyncio
    async def test_dollar_brace_blocked(self, tool):
        result = await tool.execute("echo ${HOME}")
        assert "injection" in result.lower() or "blocked" in result.lower()

    @pytest.mark.asyncio
    async def test_heredoc_blocked(self, tool):
        result = await tool.execute("cat << EOF\nhello\nEOF")
        assert "injection" in result.lower() or "blocked" in result.lower()


class TestSafeCommandsAllowed:
    """Test that safe commands still work."""

    @pytest.mark.asyncio
    async def test_simple_ls(self, tool):
        result = await tool.execute("ls")
        # Should not be blocked
        assert "injection" not in result.lower()
        assert "blocked" not in result.lower()

    @pytest.mark.asyncio
    async def test_echo(self, tool):
        result = await tool.execute("echo hello")
        assert "hello" in result

    @pytest.mark.asyncio
    async def test_python_version(self, tool):
        result = await tool.execute("python3 --version")
        assert "python" in result.lower() or "Python" in result


class TestDenyPatterns:
    """Test dangerous command patterns are blocked."""

    @pytest.mark.asyncio
    async def test_rm_rf_blocked(self, tool):
        result = await tool.execute("rm -rf /tmp/somedir")
        assert "blocked" in result.lower()

    @pytest.mark.asyncio
    async def test_shutdown_blocked(self, tool):
        result = await tool.execute("shutdown now")
        assert "blocked" in result.lower()


class TestWorkspaceRestriction:
    """Test workspace path restriction."""

    @pytest.mark.asyncio
    async def test_traversal_blocked(self, restricted_tool):
        result = await restricted_tool.execute("cat ../../../etc/passwd")
        assert "blocked" in result.lower()
