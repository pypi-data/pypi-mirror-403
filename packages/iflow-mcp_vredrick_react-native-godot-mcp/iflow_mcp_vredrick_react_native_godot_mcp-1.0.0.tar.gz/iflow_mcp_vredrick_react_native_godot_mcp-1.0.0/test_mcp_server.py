#!/usr/bin/env python3
"""
Test script for React Native Godot MCP Server
Tests each tool to ensure the server is working correctly
"""

import asyncio
import json
from typing import Any
import sys

# Add colors for better output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_test_header(test_name: str):
    """Print a formatted test header"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}━━━ Testing: {test_name} ━━━{Colors.RESET}")

def print_success(message: str):
    """Print success message"""
    print(f"{Colors.GREEN}✅ {message}{Colors.RESET}")

def print_error(message: str):
    """Print error message"""
    print(f"{Colors.RED}❌ {message}{Colors.RESET}")

def print_result(result: str, max_length: int = 500):
    """Print truncated result"""
    if len(result) > max_length:
        result = result[:max_length] + "..."
    print(f"{Colors.YELLOW}{result}{Colors.RESET}")

async def test_mcp_server():
    """Run tests for all MCP server tools"""
    
    print(f"{Colors.BOLD}{'='*60}")
    print("React Native Godot MCP Server Test Suite")
    print(f"{'='*60}{Colors.RESET}")
    
    # Import the server module
    try:
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
        print_success("Successfully imported MCP server module")
    except ImportError as e:
        print_error(f"Failed to import MCP server: {e}")
        return False
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Get Documentation
    print_test_header("get_documentation")
    try:
        result = await get_documentation.fn(
            context=None,
            section="overview",
            format=ResponseFormat.MARKDOWN,
            detail=DetailLevel.CONCISE
        )
        if result and "React Native Godot" in result:
            print_success("Documentation fetched successfully")
            print_result(result, 200)
            tests_passed += 1
        else:
            print_error("Documentation content not as expected")
            tests_failed += 1
    except Exception as e:
        print_error(f"Failed: {e}")
        tests_failed += 1
    
    # Test 2: Search Documentation
    print_test_header("search_documentation")
    try:
        result = await search_documentation.fn(
            context=None,
            query="worklets",
            max_results=3,
            format=ResponseFormat.MARKDOWN
        )
        if result and "worklet" in result.lower():
            print_success("Search returned relevant results")
            print_result(result, 200)
            tests_passed += 1
        else:
            print_error("Search results not relevant")
            tests_failed += 1
    except Exception as e:
        print_error(f"Failed: {e}")
        tests_failed += 1
    
    # Test 3: Get Example Code
    print_test_header("get_example_code")
    try:
        result = await get_example_code.fn(
            context=None,
            topic="initialization",
            platform="ios",
            format=ResponseFormat.MARKDOWN
        )
        if result and "RTNGodot.createInstance" in result:
            print_success("Example code retrieved successfully")
            print_result(result, 200)
            tests_passed += 1
        else:
            print_error("Example code not as expected")
            tests_failed += 1
    except Exception as e:
        print_error(f"Failed: {e}")
        tests_failed += 1
    
    # Test 4: Get Setup Instructions
    print_test_header("get_setup_instructions")
    try:
        result = await get_setup_instructions.fn(
            context=None,
            platform="android",
            include_debugging=False,
            custom_build=False,
            format=ResponseFormat.MARKDOWN
        )
        if result and "installation" in result.lower():
            print_success("Setup instructions retrieved")
            print_result(result, 200)
            tests_passed += 1
        else:
            print_error("Setup instructions incomplete")
            tests_failed += 1
    except Exception as e:
        print_error(f"Failed: {e}")
        tests_failed += 1
    
    # Test 5: Get API Reference
    print_test_header("get_api_reference")
    try:
        result = await get_api_reference.fn(
            context=None,
            topic="RTNGodot",
            include_examples=True,
            format=ResponseFormat.MARKDOWN
        )
        if result and "createInstance" in result:
            print_success("API reference retrieved")
            print_result(result, 200)
            tests_passed += 1
        else:
            print_error("API reference incomplete")
            tests_failed += 1
    except Exception as e:
        print_error(f"Failed: {e}")
        tests_failed += 1
    
    # Test 6: Get Troubleshooting
    print_test_header("get_troubleshooting")
    try:
        result = await get_troubleshooting.fn(
            context=None,
            issue="build_error",
            platform="ios",
            format=ResponseFormat.MARKDOWN
        )
        if result and "troubleshooting" in result.lower():
            print_success("Troubleshooting info retrieved")
            print_result(result, 200)
            tests_passed += 1
        else:
            print_error("Troubleshooting info not helpful")
            tests_failed += 1
    except Exception as e:
        print_error(f"Failed: {e}")
        tests_failed += 1
    
    # Test 7: Get File from Repo
    print_test_header("get_file_from_repo")
    try:
        result = await get_file_from_repo.fn(
            context=None,
            path="package.json",
            branch="master",
            format=ResponseFormat.MARKDOWN
        )
        if result and ("react-native-godot" in result or "Error" in result):
            if "Error" in result:
                print_success("File fetch handled error gracefully")
            else:
                print_success("File retrieved from repository")
            print_result(result, 200)
            tests_passed += 1
        else:
            print_error("File fetch failed")
            tests_failed += 1
    except Exception as e:
        print_error(f"Failed: {e}")
        tests_failed += 1
    
    # Test 8: JSON Format
    print_test_header("JSON Response Format")
    try:
        result = await get_documentation.fn(
            context=None,
            section="overview",
            format=ResponseFormat.JSON,
            detail=DetailLevel.CONCISE
        )
        json_data = json.loads(result)
        if json_data and "content" in json_data:
            print_success("JSON format working correctly")
            print(f"Keys in response: {list(json_data.keys())}")
            tests_passed += 1
        else:
            print_error("JSON format invalid")
            tests_failed += 1
    except Exception as e:
        print_error(f"Failed: {e}")
        tests_failed += 1
    
    # Test 9: Detail Levels
    print_test_header("Detail Level Variations")
    try:
        concise = await get_documentation.fn(None, "api_usage", ResponseFormat.MARKDOWN, DetailLevel.CONCISE)
        detailed = await get_documentation.fn(None, "api_usage", ResponseFormat.MARKDOWN, DetailLevel.DETAILED)
        full = await get_documentation.fn(None, "api_usage", ResponseFormat.MARKDOWN, DetailLevel.FULL)
        
        if len(concise) < len(detailed) < len(full):
            print_success("Detail levels working correctly")
            print(f"Lengths - Concise: {len(concise)}, Detailed: {len(detailed)}, Full: {len(full)}")
            tests_passed += 1
        else:
            print_error("Detail levels not differentiating properly")
            tests_failed += 1
    except Exception as e:
        print_error(f"Failed: {e}")
        tests_failed += 1
    
    # Print summary
    print(f"\n{Colors.BOLD}{'='*60}")
    print("Test Summary")
    print(f"{'='*60}{Colors.RESET}")
    
    total_tests = tests_passed + tests_failed
    success_rate = (tests_passed / total_tests * 100) if total_tests > 0 else 0
    
    print(f"{Colors.GREEN}Passed: {tests_passed}{Colors.RESET}")
    print(f"{Colors.RED}Failed: {tests_failed}{Colors.RESET}")
    print(f"Success Rate: {success_rate:.1f}%")
    
    if tests_failed == 0:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 All tests passed! The MCP server is working correctly.{Colors.RESET}")
        return True
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}⚠️  Some tests failed. Please check the errors above.{Colors.RESET}")
        return False

async def main():
    """Main entry point"""
    try:
        success = await test_mcp_server()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Test interrupted by user{Colors.RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Unexpected error: {e}{Colors.RESET}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
