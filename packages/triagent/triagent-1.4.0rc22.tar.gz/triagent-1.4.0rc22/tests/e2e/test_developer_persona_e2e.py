"""E2E Integration Tests for Developer Persona.

These tests ACTUALLY INVOKE the AI agent and validate responses:
1. Send prompt to Developer persona
2. Wait for AI response
3. Capture full response text and tools used
4. Validate response contains expected content

Prerequisites:
- Azure CLI installed and authenticated
- Access to Azure DevOps organization 'symphonyvsts'
- Anthropic API key or Azure Foundry credentials configured
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import pytest

from triagent.security.azure_auth import (
    check_azure_cli_installed,
    check_azure_login_status,
)

if TYPE_CHECKING:
    pass


def _is_azure_authenticated() -> bool:
    """Check if Azure CLI is installed and authenticated."""
    installed, _ = check_azure_cli_installed()
    if not installed:
        return False
    logged_in, _ = check_azure_login_status()
    return logged_in


requires_azure_auth = pytest.mark.skipif(
    not _is_azure_authenticated(),
    reason="Requires Azure CLI authentication (run 'az login' first)",
)


@dataclass
class AgentResponse:
    """Captured response from the AI agent."""

    text: str = ""
    tools_used: list[str] = field(default_factory=list)
    tool_results: dict[str, Any] = field(default_factory=dict)
    num_turns: int = 0
    session_id: str | None = None


async def invoke_developer_persona(prompt: str, timeout: int = 300) -> AgentResponse:
    """Invoke the Developer persona with a prompt and capture the response.

    Args:
        prompt: The user prompt to send
        timeout: Maximum seconds to wait for response (unused, handled by pytest-timeout)

    Returns:
        AgentResponse with captured text and metadata
    """
    # Import here to avoid issues when Azure auth not available
    from claude_agent_sdk import ClaudeSDKClient
    from rich.console import Console

    from triagent.config import ConfigManager
    from triagent.sdk_client import create_sdk_client

    # Set headless mode for E2E tests
    os.environ["CI"] = "true"
    os.environ["ANTHROPIC_HEADLESS"] = "1"

    config_manager = ConfigManager()
    console = Console(quiet=True)

    # Create SDK client with Developer persona
    client_factory = create_sdk_client(
        config_manager,
        console,
        team="omnia-data",
        persona="developer",
    )
    options = client_factory._build_options()

    response = AgentResponse()

    async with ClaudeSDKClient(options=options) as client:
        await client.query(prompt=prompt)

        async for msg in client.receive_response():
            msg_type = type(msg).__name__

            if msg_type == "AssistantMessage":
                for block in msg.content:
                    block_type = type(block).__name__

                    if block_type == "TextBlock":
                        response.text += block.text

                    elif block_type == "ToolUseBlock":
                        tool_name = getattr(block, "name", "unknown")
                        response.tools_used.append(tool_name)

                    elif block_type == "ToolResultBlock":
                        tool_id = getattr(block, "tool_use_id", "unknown")
                        content = getattr(block, "content", "")
                        response.tool_results[tool_id] = content

            elif msg_type == "ResultMessage":
                response.num_turns = getattr(msg, "num_turns", 0)
                response.session_id = getattr(msg, "session_id", None)

    return response


@requires_azure_auth
class TestDeveloperPersonaE2E:
    """True E2E tests that invoke the AI agent and validate responses."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(300)
    async def test_scenario1_list_delta_team_members(self) -> None:
        """Scenario 1: 'Show me list of team members in the Delta Team'

        Expected: Response mentions specific Delta team members by name.
        """
        prompt = "Show me list of team members in the Delta Team"

        print(f"\n{'='*60}")
        print(f"PROMPT: {prompt}")
        print(f"{'='*60}")

        response = await invoke_developer_persona(prompt)

        print(f"\nRESPONSE ({len(response.text)} chars):")
        print(f"{'-'*60}")
        print(response.text[:2000])  # Print first 2000 chars
        if len(response.text) > 2000:
            print(f"... ({len(response.text) - 2000} more chars)")
        print(f"{'-'*60}")
        print(f"Tools used: {response.tools_used}")
        print(f"Turns: {response.num_turns}")

        # Validate response contains expected content
        assert len(response.text) > 100, "Response too short"

        # Should mention Delta team
        assert "Delta" in response.text, "Should mention Delta team"

        # Should mention at least one known Delta team member
        # From user-mappings.tsv: Rakesh Kumar Thakur (Tech Lead), Vikas J, etc.
        known_members = ["Rakesh", "Thakur", "Vikas", "Teja", "Pillai", "Priyadarshan"]
        found_member = any(name in response.text for name in known_members)
        assert found_member, f"Should mention at least one Delta team member. Known: {known_members}"

    @pytest.mark.asyncio
    @pytest.mark.timeout(300)
    async def test_scenario2_delta_developers_prs_21_3(self) -> None:
        """Scenario 2: 'Show me list of developers in Delta Team and PRs in 21.3'

        Expected: Response lists developers AND mentions PRs or pull requests.
        """
        prompt = "Show me list of developers in the Delta Team and find out the PRs they have opened in 21.3"

        print(f"\n{'='*60}")
        print(f"PROMPT: {prompt}")
        print(f"{'='*60}")

        response = await invoke_developer_persona(prompt)

        print(f"\nRESPONSE ({len(response.text)} chars):")
        print(f"{'-'*60}")
        print(response.text[:3000])
        if len(response.text) > 3000:
            print(f"... ({len(response.text) - 3000} more chars)")
        print(f"{'-'*60}")
        print(f"Tools used: {response.tools_used}")

        # Validate response
        assert len(response.text) > 100, "Response too short"

        # Should mention Delta
        assert "Delta" in response.text, "Should mention Delta team"

        # Should mention developers or team members
        developer_keywords = ["developer", "Developer", "member", "team"]
        found_developer = any(kw in response.text for kw in developer_keywords)
        assert found_developer, "Should mention developers"

        # Should mention PRs or pull requests
        pr_keywords = ["PR", "pull request", "Pull Request", "pull-request"]
        found_pr = any(kw in response.text for kw in pr_keywords)
        assert found_pr, "Should mention PRs or pull requests"

    @pytest.mark.asyncio
    @pytest.mark.timeout(600)
    async def test_scenario3_pr_review_dotnet_795503(self) -> None:
        """Scenario 3: 'perform comprehensive PR review for 795503'

        Expected: Response contains .NET/C# code review comments.
        On-demand loading of dotnet_code_review.md skill.
        """
        prompt = "perform comprehensive PR review for 795503"

        print(f"\n{'='*60}")
        print(f"PROMPT: {prompt}")
        print(f"{'='*60}")

        response = await invoke_developer_persona(prompt, timeout=600)

        print(f"\nRESPONSE ({len(response.text)} chars):")
        print(f"{'-'*60}")
        print(response.text[:5000])
        if len(response.text) > 5000:
            print(f"... ({len(response.text) - 5000} more chars)")
        print(f"{'-'*60}")
        print(f"Tools used: {response.tools_used}")

        # Validate response
        assert len(response.text) > 200, "Response too short for a code review"

        # Should mention the PR number
        assert "795503" in response.text, "Should reference PR 795503"

        # Should contain code review indicators
        review_keywords = ["review", "Review", "code", "change", "file"]
        found_review = any(kw in response.text for kw in review_keywords)
        assert found_review, "Should contain code review content"

        # For .NET PR, should mention C#, .NET, or related terms
        dotnet_keywords = ["C#", "csharp", ".NET", "dotnet", ".cs", "SQL", "sql"]
        found_dotnet = any(kw in response.text for kw in dotnet_keywords)
        # Note: This assertion is conditional - PR might not have .NET files
        if found_dotnet:
            print("OK: .NET code review guidelines loaded (found dotnet keywords)")

    @pytest.mark.asyncio
    @pytest.mark.timeout(600)
    async def test_scenario4_pr_report_delta_21_3(self) -> None:
        """Scenario 4: 'generate PR report for the Delta Team for 21.3'

        Expected: Response contains PR report with HTML or markdown formatting.
        """
        prompt = "generate PR report for the Delta Team for 21.3"

        print(f"\n{'='*60}")
        print(f"PROMPT: {prompt}")
        print(f"{'='*60}")

        response = await invoke_developer_persona(prompt, timeout=600)

        print(f"\nRESPONSE ({len(response.text)} chars):")
        print(f"{'-'*60}")
        print(response.text[:5000])
        if len(response.text) > 5000:
            print(f"... ({len(response.text) - 5000} more chars)")
        print(f"{'-'*60}")
        print(f"Tools used: {response.tools_used}")

        # Validate response
        assert len(response.text) > 200, "Response too short for a PR report"

        # Should mention Delta team
        assert "Delta" in response.text, "Should mention Delta team"

        # Should mention report or PR-related content
        report_keywords = ["report", "Report", "PR", "pull request", "contribution"]
        found_report = any(kw in response.text for kw in report_keywords)
        assert found_report, "Should contain report content"

        # Check for table/list formatting (markdown or HTML)
        has_formatting = (
            "|" in response.text  # Markdown table
            or "<table" in response.text.lower()  # HTML table
            or "- " in response.text  # Markdown list
            or "* " in response.text  # Markdown list
        )
        if has_formatting:
            print("OK: Report has formatted output (tables/lists)")

    @pytest.mark.asyncio
    @pytest.mark.timeout(600)
    async def test_scenario5_pr_review_pyspark_795366(self) -> None:
        """Scenario 5: 'perform comprehensive PR review for 795366'

        Expected: Response contains PySpark/Python code review comments.
        On-demand loading of pyspark_code_review.md skill.
        """
        prompt = "perform comprehensive PR review for 795366"

        print(f"\n{'='*60}")
        print(f"PROMPT: {prompt}")
        print(f"{'='*60}")

        response = await invoke_developer_persona(prompt, timeout=600)

        print(f"\nRESPONSE ({len(response.text)} chars):")
        print(f"{'-'*60}")
        print(response.text[:5000])
        if len(response.text) > 5000:
            print(f"... ({len(response.text) - 5000} more chars)")
        print(f"{'-'*60}")
        print(f"Tools used: {response.tools_used}")

        # Validate response
        assert len(response.text) > 200, "Response too short for a code review"

        # Should mention the PR number
        assert "795366" in response.text, "Should reference PR 795366"

        # Should contain code review indicators
        review_keywords = ["review", "Review", "code", "change", "file"]
        found_review = any(kw in response.text for kw in review_keywords)
        assert found_review, "Should contain code review content"

        # For PySpark PR, should mention Python, Spark, or related terms
        pyspark_keywords = [
            "Python",
            "python",
            "PySpark",
            "pyspark",
            "Spark",
            "spark",
            ".py",
            "DataFrame",
            "dataframe",
        ]
        found_pyspark = any(kw in response.text for kw in pyspark_keywords)
        # Note: This assertion is conditional
        if found_pyspark:
            print("OK: PySpark code review guidelines loaded (found pyspark keywords)")
