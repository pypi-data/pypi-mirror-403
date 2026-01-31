"""Example using WebSearch to research and compare multiple topics.

This example demonstrates a research task that requires multiple web searches
to gather information and synthesize a comparison.

Before running, set your API key:
    export CLAUDE_TRACES_API_KEY=ct_...

Or inline:
    CLAUDE_TRACES_API_KEY=ct_... uv run python examples/web_research.py
"""

import asyncio

from claude_code_sdk import (
    AssistantMessage,
    ClaudeCodeOptions,
    ResultMessage,
    SystemMessage,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
    query,
)

from claude_traces_client import traced


# ANSI color codes
class Colors:
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"


def format_message(message) -> str:
    """Format a message for pretty printing."""
    lines = []

    if isinstance(message, SystemMessage):
        lines.append(f"{Colors.BLUE}{Colors.BOLD}=== SYSTEM MESSAGE ==={Colors.RESET}")
        lines.append(f"{Colors.BLUE}subtype:{Colors.RESET} {message.subtype}")
        if message.data:
            lines.append(f"{Colors.BLUE}session_id:{Colors.RESET} {message.data.get('session_id', 'N/A')}")
            lines.append(f"{Colors.BLUE}model:{Colors.RESET} {message.data.get('model', 'N/A')}")
            tools = message.data.get("tools", [])
            if tools:
                lines.append(f"{Colors.BLUE}tools:{Colors.RESET} {', '.join(tools[:5])}{'...' if len(tools) > 5 else ''}")

    elif isinstance(message, UserMessage):
        lines.append(f"{Colors.GREEN}{Colors.BOLD}=== USER MESSAGE ==={Colors.RESET}")
        content = message.content
        if isinstance(content, str):
            lines.append(f"{Colors.GREEN}content:{Colors.RESET}")
            lines.append(f"  {content}")
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, ToolResultBlock):
                    lines.append(f"{Colors.GREEN}tool_result:{Colors.RESET} {block.tool_use_id}")
                    result_str = str(block.content) if block.content else "None"
                    if len(result_str) > 200:
                        result_str = result_str[:200] + "..."
                    lines.append(f"  {result_str}")

    elif isinstance(message, AssistantMessage):
        lines.append(f"{Colors.YELLOW}{Colors.BOLD}=== ASSISTANT MESSAGE ==={Colors.RESET}")
        lines.append(f"{Colors.YELLOW}model:{Colors.RESET} {message.model}")
        for block in message.content:
            if isinstance(block, TextBlock):
                lines.append(f"{Colors.YELLOW}text:{Colors.RESET}")
                for line in block.text.split("\n"):
                    lines.append(f"  {line}")
            elif isinstance(block, ToolUseBlock):
                lines.append(f"{Colors.CYAN}tool_use:{Colors.RESET} {block.name}")
                lines.append(f"  {Colors.DIM}id:{Colors.RESET} {block.id}")
                lines.append(f"  {Colors.DIM}input:{Colors.RESET} {block.input}")

    elif isinstance(message, ResultMessage):
        lines.append(f"{Colors.MAGENTA}{Colors.BOLD}=== RESULT ==={Colors.RESET}")
        lines.append(f"{Colors.MAGENTA}session_id:{Colors.RESET} {message.session_id}")
        lines.append(f"{Colors.MAGENTA}duration_ms:{Colors.RESET} {message.duration_ms}")
        lines.append(f"{Colors.MAGENTA}num_turns:{Colors.RESET} {message.num_turns}")
        lines.append(f"{Colors.MAGENTA}is_error:{Colors.RESET} {message.is_error}")
        if message.total_cost_usd:
            lines.append(f"{Colors.MAGENTA}total_cost_usd:{Colors.RESET} ${message.total_cost_usd:.4f}")
        if message.result:
            lines.append(f"{Colors.MAGENTA}result:{Colors.RESET}")
            for line in message.result.split("\n"):
                lines.append(f"  {line}")

    else:
        lines.append(f"{Colors.DIM}=== UNKNOWN MESSAGE ==={Colors.RESET}")
        lines.append(str(message))

    return "\n".join(lines)


async def main():
    # This prompt requires multiple web searches:
    # 1. Search for Cursor IDE features/pricing
    # 2. Search for Windsurf IDE features/pricing
    # 3. Search for recent reviews/comparisons
    # Then synthesize into a recommendation
    prompt = """Compare Cursor and Windsurf as AI-powered code editors.

Research both tools and provide:
1. Key features of each
2. Pricing comparison
3. Recent user reviews or notable opinions
4. Your recommendation for different use cases

Use WebSearch to gather current information about both tools."""

    async for msg in traced(
        query(
            prompt=prompt,
            options=ClaudeCodeOptions(
                max_turns=15,
                permission_mode="bypassPermissions",
            ),
        ),
    ):
        print(format_message(msg))
        print()


if __name__ == "__main__":
    asyncio.run(main())
