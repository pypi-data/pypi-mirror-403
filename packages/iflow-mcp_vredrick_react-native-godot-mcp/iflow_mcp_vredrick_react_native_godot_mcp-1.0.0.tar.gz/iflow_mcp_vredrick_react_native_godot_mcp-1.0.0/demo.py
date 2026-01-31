#!/usr/bin/env python3
"""
Demo script for React Native Godot MCP Server
Showcases all available tools and their capabilities
"""

import asyncio
from react_native_godot_mcp import (
    get_documentation,
    search_documentation,
    get_example_code,
    get_setup_instructions,
    get_api_reference,
    get_troubleshooting,
    get_file_from_repo,
    ResponseFormat,
    DetailLevel
)

# ANSI color codes for pretty output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_demo_header(title: str):
    """Print a fancy demo header"""
    print(f"\n{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.HEADER}{title:^70}{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*70}{Colors.RESET}\n")

def print_tool_demo(tool_name: str, description: str):
    """Print tool demonstration header"""
    print(f"\n{Colors.GREEN}▶ {Colors.BOLD}{tool_name}{Colors.RESET}")
    print(f"{Colors.BLUE}  {description}{Colors.RESET}\n")

def print_output(content: str, max_lines: int = 15):
    """Print truncated output with formatting"""
    lines = content.split('\n')
    if len(lines) > max_lines:
        for line in lines[:max_lines]:
            print(f"  {line}")
        print(f"\n{Colors.YELLOW}  ... (output truncated, showing {max_lines}/{len(lines)} lines) ...{Colors.RESET}\n")
    else:
        for line in lines:
            print(f"  {line}")

async def run_demo():
    """Run the complete demo of all MCP server capabilities"""
    
    print_demo_header("React Native Godot MCP Server Demo")
    
    print(f"{Colors.BOLD}Welcome to the React Native Godot Documentation MCP Server!{Colors.RESET}")
    print("This demo will showcase all available tools and their capabilities.")
    print("Each tool is designed to help LLMs efficiently access React Native Godot documentation.\n")
    
    input(f"{Colors.YELLOW}Press Enter to start the demo...{Colors.RESET}")
    
    # Demo 1: Get Documentation
    print_tool_demo(
        "get_documentation",
        "Fetches specific sections of documentation with adjustable detail levels"
    )
    
    print("Example: Getting threading documentation in concise format...")
    result = await get_documentation(
        None,
        section="threading",
        format=ResponseFormat.MARKDOWN,
        detail=DetailLevel.CONCISE
    )
    print_output(result, 10)
    
    # Demo 2: Search Documentation
    print_tool_demo(
        "search_documentation",
        "Intelligently searches across all documentation for specific topics"
    )
    
    print("Example: Searching for information about 'signals'...")
    result = await search_documentation(
        None,
        query="signals connect JavaScript",
        max_results=2,
        format=ResponseFormat.MARKDOWN
    )
    print_output(result, 15)
    
    # Demo 3: Get Example Code
    print_tool_demo(
        "get_example_code", 
        "Provides working code examples for various features"
    )
    
    print("Example: Getting worklets example code...")
    result = await get_example_code(
        None,
        topic="worklets",
        platform="both",
        format=ResponseFormat.MARKDOWN
    )
    print_output(result, 20)
    
    # Demo 4: Get Setup Instructions
    print_tool_demo(
        "get_setup_instructions",
        "Provides platform-specific setup and configuration guidance"
    )
    
    print("Example: Getting iOS setup instructions with debugging...")
    result = await get_setup_instructions(
        None,
        platform="ios",
        include_debugging=True,
        custom_build=False,
        format=ResponseFormat.MARKDOWN
    )
    print_output(result, 15)
    
    # Demo 5: Get API Reference
    print_tool_demo(
        "get_api_reference",
        "Detailed API documentation with usage examples"
    )
    
    print("Example: Getting RTNGodotView component reference...")
    result = await get_api_reference(
        None,
        topic="RTNGodotView",
        include_examples=True,
        format=ResponseFormat.MARKDOWN
    )
    print_output(result, 15)
    
    # Demo 6: Get Troubleshooting
    print_tool_demo(
        "get_troubleshooting",
        "Solutions for common problems and issues"
    )
    
    print("Example: Troubleshooting view display issues...")
    result = await get_troubleshooting(
        None,
        issue="view_not_showing",
        platform=None,
        format=ResponseFormat.MARKDOWN
    )
    print_output(result, 15)
    
    # Demo 7: Get File from Repo
    print_tool_demo(
        "get_file_from_repo",
        "Direct access to any file in the repository"
    )
    
    print("Example: Fetching package.json from the repository...")
    result = await get_file_from_repo(
        None,
        path="package.json",
        branch="main",
        format=ResponseFormat.MARKDOWN
    )
    print_output(result, 10)
    
    # Demo complete
    print_demo_header("Demo Complete!")
    
    print(f"{Colors.GREEN}{Colors.BOLD}✨ Demonstration finished successfully!{Colors.RESET}\n")
    print("This MCP server provides comprehensive access to React Native Godot documentation.")
    print("\nKey features demonstrated:")
    print(f"  • {Colors.CYAN}7 specialized tools{Colors.RESET} for different documentation needs")
    print(f"  • {Colors.CYAN}Configurable detail levels{Colors.RESET} (concise, detailed, full)")
    print(f"  • {Colors.CYAN}Multiple response formats{Colors.RESET} (Markdown, JSON)")
    print(f"  • {Colors.CYAN}Platform-specific guidance{Colors.RESET} (iOS, Android, both)")
    print(f"  • {Colors.CYAN}Intelligent search{Colors.RESET} with relevance scoring")
    print(f"  • {Colors.CYAN}Direct repository access{Colors.RESET} for any file")
    
    print(f"\n{Colors.YELLOW}Ready for integration with Claude Desktop or any MCP client!{Colors.RESET}")
    print(f"\nFor setup instructions, see: {Colors.BLUE}CONFIGURATION.md{Colors.RESET}")
    print(f"For testing, run: {Colors.BLUE}python3 test_mcp_server.py{Colors.RESET}")
    
    # Bonus: Show JSON format capability
    print(f"\n{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}Bonus: JSON Response Format{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*70}{Colors.RESET}\n")
    
    print("The server also supports JSON responses for programmatic use:")
    result = await get_documentation(
        None,
        section="overview",
        format=ResponseFormat.JSON,
        detail=DetailLevel.CONCISE
    )
    
    import json
    json_data = json.loads(result)
    print(f"\nJSON Response Keys: {list(json_data.keys())}")
    print(f"Content Length: {json_data.get('length', 0)} characters")
    print(f"Title: {json_data.get('title', 'N/A')}")

async def main():
    """Main entry point"""
    try:
        await run_demo()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Demo interrupted by user{Colors.RESET}")
    except Exception as e:
        print(f"\n{Colors.RED}Error running demo: {e}{Colors.RESET}")

if __name__ == "__main__":
    print(f"{Colors.BOLD}React Native Godot MCP Server - Interactive Demo{Colors.RESET}")
    asyncio.run(main())
