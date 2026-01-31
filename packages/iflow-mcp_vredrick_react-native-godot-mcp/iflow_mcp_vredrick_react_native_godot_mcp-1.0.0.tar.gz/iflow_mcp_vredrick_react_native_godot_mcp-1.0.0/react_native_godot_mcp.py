#!/usr/bin/env python3
"""
React Native Godot MCP Server
A Model Context Protocol server for fetching and searching documentation
from the react-native-godot repository by Born.com and Migeran.

This MCP server provides intelligent access to React Native Godot documentation,
examples, and implementation details to help developers integrate Godot Engine
into React Native applications.
"""

import asyncio
import json
import re
from typing import Optional, Dict, Any, List, Literal
from enum import Enum
from pydantic import BaseModel, Field
import httpx
from fastmcp import FastMCP, Context

# Initialize FastMCP server
mcp = FastMCP(
    name="react-native-godot-docfetcher",
    version="1.0.0"
)

# Configuration
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/borndotcom/react-native-godot"
GITHUB_API_BASE = "https://api.github.com/repos/borndotcom/react-native-godot"
DEFAULT_BRANCH = "master"
CHARACTER_LIMIT = 25000
REQUEST_TIMEOUT = 30

# Documentation sections mapping
DOC_SECTIONS = {
    "overview": "Main features and capabilities",
    "installation": "NPM installation and LibGodot setup",
    "initialization": "Creating and configuring Godot instances", 
    "api_usage": "Accessing Godot API from TypeScript/JavaScript",
    "threading": "JavaScript threading and worklets",
    "godot_views": "Embedding Godot views in React Native",
    "export": "Exporting Godot projects for React Native",
    "debugging": "Native and remote debugging setup",
    "custom_builds": "Using custom LibGodot builds",
    "examples": "Example application and code snippets"
}

class ResponseFormat(str, Enum):
    """Response format options"""
    MARKDOWN = "markdown"
    JSON = "json"
    
class DetailLevel(str, Enum):
    """Level of detail in responses"""
    CONCISE = "concise"
    DETAILED = "detailed"
    FULL = "full"

# === Input Models ===

class GetDocumentationInput(BaseModel):
    """Input for fetching specific documentation sections"""
    section: Optional[str] = Field(
        None,
        description=f"Documentation section to fetch. Options: {', '.join(DOC_SECTIONS.keys())}. If not specified, returns overview."
    )
    format: ResponseFormat = Field(
        ResponseFormat.MARKDOWN,
        description="Response format: 'markdown' for formatted text, 'json' for structured data"
    )
    detail: DetailLevel = Field(
        DetailLevel.DETAILED,
        description="Level of detail: 'concise' (key points only), 'detailed' (with examples), 'full' (complete content)"
    )

class SearchDocumentationInput(BaseModel):
    """Input for searching documentation"""
    query: str = Field(
        ...,
        description="Search query. Examples: 'worklets', 'Android setup', 'Godot signals', 'debugging iOS'"
    )
    max_results: int = Field(
        5,
        ge=1,
        le=20,
        description="Maximum number of results to return"
    )
    format: ResponseFormat = Field(
        ResponseFormat.MARKDOWN,
        description="Response format"
    )

class GetExampleCodeInput(BaseModel):
    """Input for fetching example code"""
    topic: str = Field(
        ...,
        description="Topic for example code. Options: 'initialization', 'api_usage', 'signals', 'views', 'worklets', 'complete_app'"
    )
    platform: Optional[Literal["ios", "android", "both"]] = Field(
        "both",
        description="Target platform for examples"
    )
    format: ResponseFormat = Field(
        ResponseFormat.MARKDOWN,
        description="Response format"
    )

class GetSetupInstructionsInput(BaseModel):
    """Input for getting setup instructions"""
    platform: Literal["ios", "android", "both"] = Field(
        ...,
        description="Platform to get setup instructions for"
    )
    include_debugging: bool = Field(
        False,
        description="Include debugging setup instructions"
    )
    custom_build: bool = Field(
        False,
        description="Include custom LibGodot build instructions"
    )
    format: ResponseFormat = Field(
        ResponseFormat.MARKDOWN,
        description="Response format"
    )

class GetAPIReferenceInput(BaseModel):
    """Input for fetching API reference"""
    topic: str = Field(
        ...,
        description="API topic. Examples: 'RTNGodot', 'RTNGodotView', 'runOnGodotThread', 'signals', 'callables', 'properties'"
    )
    include_examples: bool = Field(
        True,
        description="Include usage examples with API reference"
    )
    format: ResponseFormat = Field(
        ResponseFormat.MARKDOWN,
        description="Response format"
    )

class GetTroubleshootingInput(BaseModel):
    """Input for troubleshooting information"""
    issue: Optional[str] = Field(
        None,
        description="Specific issue to troubleshoot. Examples: 'build error', 'view not showing', 'thread issues', 'export problems'"
    )
    platform: Optional[Literal["ios", "android"]] = Field(
        None,
        description="Platform experiencing the issue"
    )
    format: ResponseFormat = Field(
        ResponseFormat.MARKDOWN,
        description="Response format"
    )

class GetFileFromRepoInput(BaseModel):
    """Input for fetching a specific file from the repository"""
    path: str = Field(
        ...,
        description="Path to file in repository. Examples: 'README.md', 'example/App.tsx', 'package.json'"
    )
    branch: str = Field(
        DEFAULT_BRANCH,
        description="Git branch to fetch from"
    )
    format: ResponseFormat = Field(
        ResponseFormat.MARKDOWN,
        description="Response format"
    )

# === Helper Functions ===

async def fetch_readme() -> str:
    """Fetch the main README.md file"""
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        try:
            response = await client.get(f"{GITHUB_RAW_BASE}/{DEFAULT_BRANCH}/README.md")
            response.raise_for_status()
            return response.text
        except Exception as e:
            raise Exception(f"Failed to fetch README: {str(e)}")

async def fetch_file(path: str, branch: str = DEFAULT_BRANCH) -> str:
    """Fetch a file from the repository"""
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        try:
            url = f"{GITHUB_RAW_BASE}/{branch}/{path}"
            response = await client.get(url)
            response.raise_for_status()
            return response.text
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise Exception(f"File not found: {path} on branch {branch}")
            raise Exception(f"Failed to fetch file: {str(e)}")
        except Exception as e:
            raise Exception(f"Error fetching file: {str(e)}")

def extract_section(content: str, section: str) -> str:
    """Extract a specific section from markdown content"""
    lines = content.split('\n')
    result = []
    in_section = False
    section_level = 0
    
    section_patterns = {
        "overview": ["# Main Features", "Born React Native Godot", "React Native Godot allows"],
        "installation": ["# Installation", "# Getting Started", "## Installation from NPM"],
        "initialization": ["### Initialize the Godot instance", "## Initialization", "## Hello World"],
        "api_usage": ["## Godot API Usage", "### API Usage", "# Godot API Usage"],
        "threading": ["## Threading", "### Threading and JavaScript", "# Threading and JavaScript in React Native"],
        "godot_views": ["### Godot View", "## Views", "## Godot View"],
        "export": ["## Export", "### Exporting Godot", "## Export the Godot"],
        "debugging": ["## Debugging", "### Debug", "# Debugging"],
        "custom_builds": ["## Custom LibGodot", "### Custom Builds", "# Using Custom LibGodot Builds"],
        "examples": ["## Example", "### Example App", "# Getting Started with the Example"]
    }
    
    patterns = section_patterns.get(section, [f"## {section}", f"### {section}"])
    
    for i, line in enumerate(lines):
        # Check if we're entering the target section
        if not in_section:
            for pattern in patterns:
                if pattern.lower() in line.lower():
                    in_section = True
                    section_level = line.count('#')
                    result.append(line)
                    break
        else:
            # Check if we're leaving the section
            if line.startswith('#'):
                current_level = line.count('#')
                if current_level <= section_level and current_level > 0:
                    break
            result.append(line)
    
    return '\n'.join(result) if result else f"Section '{section}' not found"

def format_response(content: str, format: ResponseFormat, title: str = "") -> str:
    """Format response based on requested format"""
    if format == ResponseFormat.JSON:
        return json.dumps({
            "title": title,
            "content": content,
            "length": len(content)
        }, indent=2)
    else:
        # Markdown format
        if title:
            return f"# {title}\n\n{content}"
        return content

def truncate_content(content: str, limit: int = CHARACTER_LIMIT) -> str:
    """Truncate content to character limit while preserving structure"""
    if len(content) <= limit:
        return content
    
    # Try to truncate at a paragraph boundary
    truncated = content[:limit]
    last_para = truncated.rfind('\n\n')
    if last_para > limit * 0.8:  # If we can preserve at least 80% of content
        truncated = truncated[:last_para]
    
    return truncated + "\n\n... [Content truncated due to length]"

def adjust_detail_level(content: str, level: DetailLevel) -> str:
    """Adjust content based on detail level"""
    if level == DetailLevel.FULL:
        return content
    
    lines = content.split('\n')
    result = []
    
    if level == DetailLevel.CONCISE:
        # Keep only headers and key bullet points
        for line in lines:
            if line.startswith('#') or line.startswith('- ') or line.startswith('* '):
                result.append(line)
            elif line.strip() and not line.startswith(' ') and len(line) < 100:
                result.append(line)
    else:  # DETAILED
        # Keep most content but skip very verbose sections
        skip_patterns = ['Note:', 'NOTE:', 'npm', 'yarn', 'cd ', './']
        in_code_block = False
        
        for line in lines:
            if '```' in line:
                in_code_block = not in_code_block
            
            if not in_code_block or level == DetailLevel.DETAILED:
                skip = False
                for pattern in skip_patterns:
                    if line.strip().startswith(pattern) and level == DetailLevel.CONCISE:
                        skip = True
                        break
                if not skip:
                    result.append(line)
    
    return '\n'.join(result)

# === Tool Implementations ===

@mcp.tool(
    description="""Get documentation for React Native Godot.
    
    This tool fetches specific sections of the React Native Godot documentation,
    providing targeted information about features, setup, API usage, and more.
    
    Available sections:
    - overview: Main features and capabilities of React Native Godot
    - installation: NPM installation and LibGodot setup instructions
    - initialization: How to create and configure Godot instances
    - api_usage: Accessing the Godot API from TypeScript/JavaScript
    - threading: Understanding JavaScript threading and worklets
    - godot_views: Embedding Godot views in React Native layouts
    - export: Exporting Godot projects for use in React Native
    - debugging: Native and remote debugging setup
    - custom_builds: Using custom LibGodot builds
    - examples: Example application and code snippets
    
    Use this when you need specific documentation about React Native Godot features."""
)
async def get_documentation(
    context: Context,
    section: Optional[str] = None,
    format: ResponseFormat = ResponseFormat.MARKDOWN,
    detail: DetailLevel = DetailLevel.DETAILED
) -> str:
    """Fetch specific documentation sections from React Native Godot"""
    
    try:
        readme_content = await fetch_readme()
        
        if section and section in DOC_SECTIONS:
            content = extract_section(readme_content, section)
            title = f"React Native Godot - {section.replace('_', ' ').title()}"
        else:
            # Return overview if no section specified
            content = extract_section(readme_content, "overview")
            title = "React Native Godot Overview"
        
        content = adjust_detail_level(content, detail)
        content = truncate_content(content)
        
        return format_response(content, format, title)
        
    except Exception as e:
        error_msg = f"Error fetching documentation: {str(e)}"
        if format == ResponseFormat.JSON:
            return json.dumps({"error": error_msg})
        return f"❌ {error_msg}"

@mcp.tool(
    description="""Search React Native Godot documentation for specific topics.
    
    This tool searches through all documentation to find relevant information
    about specific topics, features, or problems.
    
    Example queries:
    - "worklets" - Find information about worklet usage
    - "Android setup" - Get Android-specific setup instructions
    - "Godot signals" - Learn about connecting to Godot signals
    - "debugging iOS" - Find iOS debugging information
    - "export parameters" - Get export configuration details
    
    Returns the most relevant sections matching your query."""
)
async def search_documentation(
    context: Context,
    query: str,
    max_results: int = 5,
    format: ResponseFormat = ResponseFormat.MARKDOWN
) -> str:
    """Search documentation for specific topics"""
    
    try:
        readme_content = await fetch_readme()
        
        # Split content into paragraphs
        paragraphs = readme_content.split('\n\n')
        
        # Score each paragraph based on query relevance
        scored_results = []
        query_lower = query.lower()
        query_words = query_lower.split()
        
        for para in paragraphs:
            if len(para.strip()) < 20:  # Skip very short paragraphs
                continue
                
            para_lower = para.lower()
            score = 0
            
            # Exact phrase match
            if query_lower in para_lower:
                score += 10
            
            # Individual word matches
            for word in query_words:
                if word in para_lower:
                    score += para_lower.count(word)
            
            # Boost for headers
            if para.startswith('#'):
                score *= 1.5
            
            # Boost for code examples
            if '```' in para:
                score *= 1.2
                
            if score > 0:
                scored_results.append((score, para))
        
        # Sort by score and take top results
        scored_results.sort(key=lambda x: x[0], reverse=True)
        top_results = scored_results[:max_results]
        
        if not top_results:
            content = f"No results found for query: '{query}'"
        else:
            results_text = []
            for i, (score, para) in enumerate(top_results, 1):
                results_text.append(f"### Result {i} (Relevance: {score:.1f})\n\n{para}")
            content = '\n\n---\n\n'.join(results_text)
        
        title = f"Search Results for '{query}'"
        content = truncate_content(content)
        
        return format_response(content, format, title)
        
    except Exception as e:
        error_msg = f"Error searching documentation: {str(e)}"
        if format == ResponseFormat.JSON:
            return json.dumps({"error": error_msg})
        return f"❌ {error_msg}"

@mcp.tool(
    description="""Get example code for React Native Godot implementation.
    
    This tool provides working code examples for various React Native Godot features.
    
    Available topics:
    - initialization: Godot instance creation and configuration
    - api_usage: Using Godot API from TypeScript
    - signals: Connecting JavaScript functions to Godot signals  
    - views: Embedding RTNGodotView components
    - worklets: Using worklets for thread-safe operations
    - complete_app: Full application example
    
    Platform options: ios, android, or both
    
    Use this when you need practical code examples."""
)
async def get_example_code(
    context: Context,
    topic: str,
    platform: Optional[str] = "both",
    format: ResponseFormat = ResponseFormat.MARKDOWN
) -> str:
    """Fetch example code for specific topics"""
    
    examples = {
        "initialization": """
## Godot Initialization Example

```typescript
import { RTNGodot, runOnGodotThread } from "@borndotcom/react-native-godot";
import * as FileSystem from 'expo-file-system/legacy';
import { Platform } from 'react-native';

function initGodot() {
  runOnGodotThread(() => {
    'worklet';
    console.log("Initializing Godot");
    
    if (Platform.OS === 'android') {
      RTNGodot.createInstance([
        "--verbose",
        "--path", "/main",
        "--rendering-driver", "opengl3",
        "--rendering-method", "gl_compatibility",
        "--display-driver", "embedded"
      ]);
    } else {
      RTNGodot.createInstance([
        "--verbose",
        "--main-pack", FileSystem.bundleDirectory + "main.pck",
        "--rendering-driver", "opengl3",
        "--rendering-method", "gl_compatibility",
        "--display-driver", "embedded"
      ]);
    }
  });
}

// In your component
useEffect(() => {
  initGodot();
  return () => {
    runOnGodotThread(() => {
      'worklet';
      RTNGodot.destroyInstance();
    });
  };
}, []);
```""",

        "api_usage": """
## Godot API Usage Example

```typescript
import { RTNGodot, runOnGodotThread } from "@borndotcom/react-native-godot";

function useGodotAPI() {
  runOnGodotThread(() => {
    'worklet';
    
    // Access Godot API
    let Godot = RTNGodot.API();
    
    // Get engine singleton
    var engine = Godot.Engine;
    
    // Access scene tree
    var sceneTree = engine.get_main_loop();
    var root = sceneTree.get_root();
    
    // Create Godot objects
    var vector = Godot.Vector2();
    vector.x = 100;
    vector.y = 200;
    
    // Find nodes in scene
    var player = root.find_child("Player", true, false);
    if (player) {
      // Call GDScript methods
      player.call("set_position", vector);
      
      // Get properties
      var health = player.get("health");
      console.log("Player health:", health);
    }
  });
}
```""",

        "signals": """
## Godot Signals Example

```typescript
import { RTNGodot, runOnGodotThread } from "@borndotcom/react-native-godot";

function connectToSignals() {
  runOnGodotThread(() => {
    'worklet';
    
    let Godot = RTNGodot.API();
    
    // Create a button and connect to its signal
    var button = Godot.Button();
    button.set_text("Click Me");
    
    // Connect JavaScript function to Godot signal
    button.pressed.connect(function() {
      console.log("Button was pressed!");
      // Handle button press
    });
    
    // Connect to custom signals from your scene
    var engine = Godot.Engine;
    var sceneTree = engine.get_main_loop();
    var root = sceneTree.get_root();
    
    var gameManager = root.find_child("GameManager", true, false);
    if (gameManager) {
      // Assuming GameManager has a 'game_over' signal
      gameManager.connect("game_over", function(score) {
        console.log("Game Over! Score:", score);
        // Update React Native UI
      });
    }
  });
}
```""",

        "views": """
## Godot Views Example

```typescript
import React from 'react';
import { View, StyleSheet } from 'react-native';
import { RTNGodotView } from "@borndotcom/react-native-godot";

const GameScreen = () => {
  return (
    <View style={styles.container}>
      {/* Main Godot window */}
      <RTNGodotView 
        style={styles.godotView}
        // No windowName means main window
      />
      
      {/* Additional Godot subwindow */}
      <RTNGodotView 
        style={styles.minimapView}
        windowName="minimap"
      />
      
      {/* React Native UI overlay */}
      <View style={styles.overlay}>
        {/* Your UI components */}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  godotView: {
    flex: 1,
    width: '100%',
    height: '100%',
  },
  minimapView: {
    position: 'absolute',
    top: 10,
    right: 10,
    width: 150,
    height: 150,
    borderRadius: 10,
  },
  overlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
  },
});

export default GameScreen;
```""",

        "worklets": """
## Worklets Example

```typescript
import { runOnGodotThread, runOnJS } from "@borndotcom/react-native-godot";
import { RTNGodot } from "@borndotcom/react-native-godot";

// State that needs to be shared
const sharedState = {
  playerHealth: 100,
  score: 0,
};

// Function that runs on Godot thread
function updateGameState() {
  'worklet';
  
  runOnGodotThread(() => {
    'worklet';
    
    let Godot = RTNGodot.API();
    var engine = Godot.Engine;
    var sceneTree = engine.get_main_loop();
    var root = sceneTree.get_root();
    
    var player = root.find_child("Player", true, false);
    if (player) {
      // Get values from Godot
      var health = player.get("health");
      var score = player.get("score");
      
      // Update shared state
      sharedState.playerHealth = health;
      sharedState.score = score;
      
      // Run UI update on JS thread
      runOnJS(() => {
        // This runs on main JS thread
        updateUIWithGameState(health, score);
      })();
    }
  });
}

// Regular JS function to update UI
function updateUIWithGameState(health: number, score: number) {
  // Update your React state here
  setPlayerHealth(health);
  setScore(score);
}

// Call periodically or on game events
useEffect(() => {
  const interval = setInterval(updateGameState, 100);
  return () => clearInterval(interval);
}, []);
```""",

        "complete_app": """
## Complete App Example

```typescript
import React, { useEffect, useState } from 'react';
import { View, Text, Button, StyleSheet } from 'react-native';
import { 
  RTNGodot, 
  RTNGodotView, 
  runOnGodotThread,
  runOnJS 
} from "@borndotcom/react-native-godot";
import * as FileSystem from 'expo-file-system/legacy';

const GameApp = () => {
  const [isGodotReady, setIsGodotReady] = useState(false);
  const [score, setScore] = useState(0);
  const [health, setHealth] = useState(100);
  
  useEffect(() => {
    initializeGodot();
    return cleanup;
  }, []);
  
  const initializeGodot = () => {
    runOnGodotThread(() => {
      'worklet';
      
      try {
        const args = Platform.OS === 'android' 
          ? ["--verbose", "--path", "/main", "--rendering-driver", "opengl3", 
             "--rendering-method", "gl_compatibility", "--display-driver", "embedded"]
          : ["--verbose", "--main-pack", FileSystem.bundleDirectory + "main.pck",
             "--rendering-driver", "opengl3", "--rendering-method", "gl_compatibility",
             "--display-driver", "embedded"];
        
        RTNGodot.createInstance(args);
        
        runOnJS(() => {
          setIsGodotReady(true);
          setupGameCallbacks();
        })();
      } catch (error) {
        console.error("Failed to initialize Godot:", error);
      }
    });
  };
  
  const setupGameCallbacks = () => {
    runOnGodotThread(() => {
      'worklet';
      
      let Godot = RTNGodot.API();
      var engine = Godot.Engine;
      var sceneTree = engine.get_main_loop();
      var root = sceneTree.get_root();
      
      // Connect to game signals
      var gameManager = root.find_child("GameManager", true, false);
      if (gameManager) {
        gameManager.connect("score_changed", function(newScore) {
          runOnJS(() => setScore(newScore))();
        });
        
        gameManager.connect("health_changed", function(newHealth) {
          runOnJS(() => setHealth(newHealth))();
        });
      }
    });
  };
  
  const cleanup = () => {
    runOnGodotThread(() => {
      'worklet';
      RTNGodot.destroyInstance();
    });
  };
  
  const pauseGame = () => {
    RTNGodot.pause();
  };
  
  const resumeGame = () => {
    RTNGodot.resume();
  };
  
  return (
    <View style={styles.container}>
      {isGodotReady ? (
        <>
          <RTNGodotView style={styles.godotView} />
          
          <View style={styles.ui}>
            <View style={styles.stats}>
              <Text style={styles.statText}>Health: {health}</Text>
              <Text style={styles.statText}>Score: {score}</Text>
            </View>
            
            <View style={styles.controls}>
              <Button title="Pause" onPress={pauseGame} />
              <Button title="Resume" onPress={resumeGame} />
            </View>
          </View>
        </>
      ) : (
        <Text style={styles.loading}>Loading Godot Engine...</Text>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  godotView: {
    flex: 1,
  },
  ui: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
  },
  stats: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    padding: 20,
    paddingTop: 50,
  },
  statText: {
    color: 'white',
    fontSize: 18,
    fontWeight: 'bold',
  },
  controls: {
    position: 'absolute',
    bottom: 30,
    left: 20,
    right: 20,
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  loading: {
    color: 'white',
    fontSize: 24,
    textAlign: 'center',
    marginTop: '50%',
  },
});

export default GameApp;
```"""
    }
    
    try:
        if topic not in examples:
            available = ", ".join(examples.keys())
            return f"❌ Unknown topic '{topic}'. Available topics: {available}"
        
        content = examples[topic]
        
        # Filter by platform if specified
        if platform and platform != "both":
            lines = content.split('\n')
            filtered = []
            in_platform_block = False
            
            for line in lines:
                if f"Platform.OS === '{platform}'" in line:
                    in_platform_block = True
                elif "Platform.OS ===" in line:
                    in_platform_block = False
                
                if platform == "both" or not "Platform.OS" in line or in_platform_block:
                    filtered.append(line)
            
            content = '\n'.join(filtered)
        
        title = f"React Native Godot - {topic.replace('_', ' ').title()} Example"
        content = truncate_content(content)
        
        return format_response(content, format, title)
        
    except Exception as e:
        error_msg = f"Error fetching example code: {str(e)}"
        if format == ResponseFormat.JSON:
            return json.dumps({"error": error_msg})
        return f"❌ {error_msg}"

@mcp.tool(
    description="""Get setup instructions for React Native Godot.
    
    This tool provides step-by-step setup instructions for integrating
    React Native Godot into your application.
    
    Options:
    - Platform: ios, android, or both
    - Include debugging setup (optional)
    - Include custom build instructions (optional)
    
    Use this when you need detailed setup and configuration instructions."""
)
async def get_setup_instructions(
    context: Context,
    platform: str,
    include_debugging: bool = False,
    custom_build: bool = False,
    format: ResponseFormat = ResponseFormat.MARKDOWN
) -> str:
    """Get detailed setup instructions"""
    
    try:
        readme_content = await fetch_readme()
        
        sections_to_include = ["installation"]
        
        if platform in ["ios", "both"]:
            sections_to_include.append("initialization")
        if platform in ["android", "both"]:
            sections_to_include.append("initialization")
        if include_debugging:
            sections_to_include.append("debugging")
        if custom_build:
            sections_to_include.append("custom_builds")
        
        combined_content = []
        for section in sections_to_include:
            section_content = extract_section(readme_content, section)
            if section_content and "not found" not in section_content:
                combined_content.append(section_content)
        
        content = "\n\n---\n\n".join(combined_content)
        
        # Add platform-specific instructions
        if platform != "both":
            lines = content.split('\n')
            filtered = []
            include_line = True
            
            for line in lines:
                if platform == "ios":
                    if "android" in line.lower() and "ios" not in line.lower():
                        include_line = False
                    elif "ios" in line.lower():
                        include_line = True
                elif platform == "android":
                    if "ios" in line.lower() and "android" not in line.lower():
                        include_line = False
                    elif "android" in line.lower():
                        include_line = True
                
                if include_line:
                    filtered.append(line)
            
            content = '\n'.join(filtered)
        
        title = f"React Native Godot Setup Instructions - {platform.title()}"
        content = truncate_content(content)
        
        return format_response(content, format, title)
        
    except Exception as e:
        error_msg = f"Error fetching setup instructions: {str(e)}"
        if format == ResponseFormat.JSON:
            return json.dumps({"error": error_msg})
        return f"❌ {error_msg}"

@mcp.tool(
    description="""Get API reference for React Native Godot.
    
    This tool provides detailed API documentation for React Native Godot
    classes, methods, and features.
    
    Topics include:
    - RTNGodot: Main API class
    - RTNGodotView: View component for embedding Godot
    - runOnGodotThread: Worklet execution function
    - signals: Signal connection and handling
    - callables: Using JS functions as Godot callables
    - properties: Accessing Godot object properties
    
    Use this when you need detailed API documentation."""
)
async def get_api_reference(
    context: Context,
    topic: str,
    include_examples: bool = True,
    format: ResponseFormat = ResponseFormat.MARKDOWN
) -> str:
    """Get API reference documentation"""
    
    api_docs = {
        "RTNGodot": """
## RTNGodot API Reference

### Class: RTNGodot

The main API class for interacting with the Godot engine from React Native.

#### Methods

##### `RTNGodot.createInstance(args: string[]): void`
Creates and initializes a new Godot instance.

**Parameters:**
- `args`: Array of command-line arguments for Godot engine

**Example:**
```typescript
RTNGodot.createInstance([
  "--verbose",
  "--main-pack", "path/to/game.pck",
  "--rendering-driver", "opengl3",
  "--display-driver", "embedded"
]);
```

##### `RTNGodot.destroyInstance(): void`
Destroys the current Godot instance. Must be called on Godot thread.

##### `RTNGodot.pause(): void`
Pauses the Godot engine execution. Called on JS main thread.

##### `RTNGodot.resume(): void`
Resumes the Godot engine execution. Called on JS main thread.

##### `RTNGodot.API(): GodotAPI`
Returns the Godot API object for accessing engine functionality.

**Returns:** GodotAPI object with access to all Godot classes and singletons.""",

        "RTNGodotView": """
## RTNGodotView API Reference

### Component: RTNGodotView

React Native component for displaying Godot engine content.

#### Props

##### `style?: ViewStyle`
Standard React Native view styles.

##### `windowName?: string`
Name of the Godot window to display. If not specified, displays the main window.

**Example:**
```tsx
// Main window
<RTNGodotView style={styles.mainView} />

// Subwindow
<RTNGodotView 
  style={styles.minimapView}
  windowName="minimap"
/>
```

#### Usage Notes

- Multiple RTNGodotView components can be used simultaneously
- Each view can display a different Godot window
- Views support all standard React Native layout and styling
- The Godot content is rendered on a separate thread""",

        "runOnGodotThread": """
## runOnGodotThread API Reference

### Function: runOnGodotThread

Executes a worklet function on the Godot thread for thread-safe operations.

#### Signature
```typescript
function runOnGodotThread(worklet: () => void): void
```

#### Parameters
- `worklet`: A function marked with 'worklet' directive

#### Important Notes

1. The function must be marked with 'worklet' directive
2. All external dependencies must be available in worklet context
3. Cannot share object references between main JS and Godot threads
4. Use for all Godot API interactions

**Example:**
```typescript
import { runOnGodotThread, runOnJS } from "@borndotcom/react-native-godot";

function interactWithGodot() {
  runOnGodotThread(() => {
    'worklet';
    
    // This runs on Godot thread
    let Godot = RTNGodot.API();
    var result = Godot.Engine.get_version_info();
    
    // To update UI, switch back to JS thread
    runOnJS(() => {
      console.log("Godot version:", result);
    })();
  });
}
```""",

        "signals": """
## Signals API Reference

### Godot Signals in React Native

Connect JavaScript functions to Godot signals for event handling.

#### Connecting to Signals

##### `object.connect(signal_name: string, callback: Function): void`
Connects a JavaScript function to a Godot signal.

##### `object.[signal_name].connect(callback: Function): void`
Alternative syntax for built-in signals.

**Example:**
```typescript
runOnGodotThread(() => {
  'worklet';
  
  let Godot = RTNGodot.API();
  
  // Method 1: Using connect method
  var node = getNodeFromScene();
  node.connect("custom_signal", function(arg1, arg2) {
    console.log("Signal received:", arg1, arg2);
  });
  
  // Method 2: Direct signal access (for built-in signals)
  var button = Godot.Button();
  button.pressed.connect(function() {
    console.log("Button pressed");
  });
});
```

#### Disconnecting Signals

##### `object.disconnect(signal_name: string, callback: Function): void`
Disconnects a previously connected callback.

#### Signal Guidelines

1. Callbacks run on the Godot thread
2. Use `runOnJS` to update React Native UI from callbacks
3. Store callback references if you need to disconnect later
4. Signals are automatically disconnected when objects are freed""",

        "callables": """
## Callables API Reference

### JavaScript Functions as Godot Callables

Pass JavaScript functions to Godot methods expecting Callable parameters.

#### Usage

JavaScript functions are automatically converted to Callables when passed to Godot methods.

**Example GDScript:**
```gdscript
extends Node
class_name JSInterface

func execute_callback(callback: Callable, data: String) -> void:
    callback.call(data)
```

**JavaScript Usage:**
```typescript
runOnGodotThread(() => {
  'worklet';
  
  let Godot = RTNGodot.API();
  var root = Godot.Engine.get_main_loop().get_root();
  var jsInterface = root.find_child("JSInterface", true, false);
  
  // Pass JS function as Callable
  jsInterface.execute_callback(
    function(data: string) {
      console.log("Received from Godot:", data);
      
      // Can interact with Godot from callback
      var processed = data.toUpperCase();
      return processed;
    },
    "Hello from Godot"
  );
});
```

#### Callable Features

1. **Arguments**: Automatically marshalled between JS and Godot
2. **Return Values**: Supported for both directions
3. **Context**: Executes in Godot thread context
4. **Lifetime**: Valid as long as the JS function exists""",

        "properties": """
## Properties API Reference

### Accessing Godot Object Properties

Get and set Godot object properties from JavaScript.

#### Getting Properties

##### Direct Access
```typescript
var value = object.property_name;
```

##### Using get() Method
```typescript
var value = object.get("property_name");
```

#### Setting Properties

##### Direct Access
```typescript
object.property_name = value;
```

##### Using set() Method
```typescript
object.set("property_name", value);
```

**Example:**
```typescript
runOnGodotThread(() => {
  'worklet';
  
  let Godot = RTNGodot.API();
  
  // Create and configure a Vector2
  var vec = Godot.Vector2();
  vec.x = 100;  // Direct property access
  vec.y = 200;
  
  // Access node properties
  var node = getNodeFromScene();
  
  // Get properties
  var position = node.position;  // Direct access
  var visible = node.get("visible");  // Using get()
  
  // Set properties
  node.position = vec;  // Direct access
  node.set("modulate", Godot.Color(1, 0, 0, 1));  // Using set()
  
  // Custom properties from GDScript
  var health = node.get("health");
  node.set("health", health + 10);
});
```

#### Property Guidelines

1. **Type Conversion**: Automatic between JS and Godot types
2. **Validation**: Godot validates property values
3. **Signals**: Setting properties may emit changed signals
4. **Performance**: Direct access is faster than get/set methods"""
    }
    
    try:
        if topic not in api_docs:
            available = ", ".join(api_docs.keys())
            return f"❌ Unknown API topic '{topic}'. Available topics: {available}"
        
        content = api_docs[topic]
        
        if not include_examples:
            # Remove example sections
            lines = content.split('\n')
            filtered = []
            in_example = False
            
            for line in lines:
                if '**Example' in line or '```' in line:
                    in_example = not in_example
                elif not in_example:
                    filtered.append(line)
            
            content = '\n'.join(filtered)
        
        title = f"React Native Godot API - {topic}"
        content = truncate_content(content)
        
        return format_response(content, format, title)
        
    except Exception as e:
        error_msg = f"Error fetching API reference: {str(e)}"
        if format == ResponseFormat.JSON:
            return json.dumps({"error": error_msg})
        return f"❌ {error_msg}"

@mcp.tool(
    description="""Get troubleshooting information for React Native Godot.
    
    This tool provides solutions to common problems and issues when
    using React Native Godot.
    
    Common issues include:
    - build error: Build and compilation problems
    - view not showing: Godot view display issues
    - thread issues: Threading and worklet problems
    - export problems: Issues with exporting Godot projects
    - performance: Performance optimization tips
    
    Platform can be specified as 'ios' or 'android' for platform-specific issues.
    
    Use this when encountering problems or errors."""
)
async def get_troubleshooting(
    context: Context,
    issue: Optional[str] = None,
    platform: Optional[str] = None,
    format: ResponseFormat = ResponseFormat.MARKDOWN
) -> str:
    """Get troubleshooting help for common issues"""
    
    troubleshooting_guide = {
        "build_error": """
## Troubleshooting Build Errors

### Common Build Issues

#### iOS Build Errors

**Issue: Module not found**
- Run `cd ios && pod install`
- Clean build folder in Xcode
- Ensure LibGodot is downloaded: `yarn download-prebuilt`

**Issue: Undefined symbols**
- Verify LibGodot.xcframework is linked
- Check "Build Phases" → "Link Binary With Libraries"
- Ensure all required frameworks are included

#### Android Build Errors

**Issue: Gradle sync failed**
- Check Java version (should be 11 or 17)
- Clean and rebuild: `cd android && ./gradlew clean`
- Verify ANDROID_HOME environment variable

**Issue: NDK not found**
- Install NDK via Android Studio SDK Manager
- Set NDK version in android/build.gradle

### General Solutions

1. **Clean Everything**
   ```bash
   cd ios && pod deintegrate && pod install
   cd ../android && ./gradlew clean
   cd .. && yarn install
   ```

2. **Reset Metro Cache**
   ```bash
   npx react-native start --reset-cache
   ```

3. **Verify Dependencies**
   ```bash
   yarn download-prebuilt
   ```""",

        "view_not_showing": """
## Troubleshooting Godot View Display Issues

### View Not Appearing

#### Check Initialization
```typescript
// Ensure Godot is initialized before rendering view
const [isReady, setIsReady] = useState(false);

useEffect(() => {
  runOnGodotThread(() => {
    'worklet';
    RTNGodot.createInstance([...args]);
    runOnJS(() => setIsReady(true))();
  });
}, []);

// Only render view when ready
{isReady && <RTNGodotView style={styles.view} />}
```

#### Verify Display Driver
- Must use `--display-driver embedded`
- Check command line arguments

#### Style Issues
```typescript
// Ensure view has dimensions
const styles = StyleSheet.create({
  godotView: {
    flex: 1,  // Or specific width/height
    width: '100%',
    height: '100%',
  }
});
```

### Black Screen

1. **Check Rendering Driver**
   - Use `--rendering-driver opengl3`
   - Use `--rendering-method gl_compatibility`

2. **Verify Pack File**
   - iOS: Check .pck file is in bundle
   - Android: Ensure assets are in correct folder

3. **Console Errors**
   - Check Xcode/Android Studio console
   - Look for Godot initialization errors""",

        "thread_issues": """
## Troubleshooting Threading Issues

### Worklet Errors

#### "Cannot find 'worklet'"
```typescript
// Ensure worklet directive is present
runOnGodotThread(() => {
  'worklet';  // This line is required!
  // Your code here
});
```

#### Object Reference Errors
```typescript
// ❌ Wrong: Sharing references across threads
const godotObj = getGodotObject(); // Main thread
runOnGodotThread(() => {
  'worklet';
  godotObj.method(); // Error!
});

// ✅ Correct: Get object in worklet
runOnGodotThread(() => {
  'worklet';
  const godotObj = getGodotObject();
  godotObj.method(); // Works!
});
```

### Thread Safety

#### Accessing Scene Tree
```typescript
// Must be on Godot thread
runOnGodotThread(() => {
  'worklet';
  let Godot = RTNGodot.API();
  var tree = Godot.Engine.get_main_loop();
  // Safe to access scene tree here
});
```

#### UI Updates
```typescript
runOnGodotThread(() => {
  'worklet';
  // Get data from Godot
  var data = getData();
  
  // Switch to JS thread for UI
  runOnJS(() => {
    setState(data);
  })();
});
```""",

        "export_problems": """
## Troubleshooting Export Issues

### Export Configuration

#### iOS Export Issues

**Problem: PCK file not found**
- Verify export preset targets iOS
- Check file path in FileSystem.bundleDirectory
- Ensure .pck is added to Xcode project

**Problem: Resources missing**
```bash
# Use provided export script
export GODOT_EDITOR=/path/to/godot
./export_godot.sh ios
```

#### Android Export Issues

**Problem: Slow asset loading**
- Use folder structure instead of .pck for Android
- Place in android/app/src/main/assets
- Use `--path` instead of `--main-pack`

### Export Script Usage

```bash
./export_godot.sh \\
  --target ./exports \\
  --project ./godot_project \\
  --name MyGame \\
  --preset "iOS" \\
  --platform ios
```

### Common Mistakes

1. **Wrong Export Format**
   - Export to PCK/ZIP, not full application
   - Don't include export templates

2. **Path Issues**
   - Use relative paths in Godot project
   - Verify resource paths after export

3. **Platform Mismatch**
   - iOS: Use .pck files
   - Android: Use folder structure""",

        "performance": """
## Performance Optimization

### Rendering Performance

#### Optimize Godot Settings
```typescript
RTNGodot.createInstance([
  "--rendering-driver", "opengl3",
  "--rendering-method", "gl_compatibility",
  "--max-fps", "60",
  "--disable-vsync",
]);
```

#### View Configuration
- Use single RTNGodotView when possible
- Minimize view resizing
- Consider render-on-demand for static content

### Memory Management

#### Clean Shutdown
```typescript
useEffect(() => {
  return () => {
    runOnGodotThread(() => {
      'worklet';
      // Clean up before destroying
      clearGameState();
      RTNGodot.destroyInstance();
    });
  };
}, []);
```

#### Resource Loading
- Load resources asynchronously
- Use resource pooling
- Preload frequently used assets

### Thread Optimization

#### Batch Operations
```typescript
runOnGodotThread(() => {
  'worklet';
  // Batch multiple operations
  updateMultipleNodes(updates);
  // Instead of multiple individual calls
});
```

#### Reduce Thread Switching
- Minimize runOnJS calls
- Batch UI updates
- Use shared state wisely"""
    }
    
    try:
        # Default to general troubleshooting if no specific issue
        if not issue:
            # Combine all troubleshooting sections
            content = "\n\n---\n\n".join(troubleshooting_guide.values())
            title = "React Native Godot - Complete Troubleshooting Guide"
        else:
            # Normalize issue name
            issue_key = issue.lower().replace(" ", "_").replace("-", "_")
            
            # Find matching troubleshooting section
            matched_content = None
            for key, value in troubleshooting_guide.items():
                if issue_key in key or key in issue_key:
                    matched_content = value
                    break
            
            if matched_content:
                content = matched_content
            else:
                # Search for issue in all sections
                relevant_sections = []
                for key, value in troubleshooting_guide.items():
                    if issue.lower() in value.lower():
                        relevant_sections.append(value)
                
                if relevant_sections:
                    content = "\n\n---\n\n".join(relevant_sections)
                else:
                    content = f"No specific troubleshooting found for '{issue}'.\n\n"
                    content += "Available troubleshooting topics:\n"
                    content += "- build_error\n- view_not_showing\n- thread_issues\n"
                    content += "- export_problems\n- performance"
            
            title = f"Troubleshooting: {issue.title()}"
        
        # Filter by platform if specified
        if platform:
            lines = content.split('\n')
            filtered = []
            other_platform = "android" if platform == "ios" else "ios"
            
            for line in lines:
                if other_platform.lower() in line.lower() and platform.lower() not in line.lower():
                    continue
                filtered.append(line)
            
            content = '\n'.join(filtered)
            title += f" ({platform.upper()})"
        
        content = truncate_content(content)
        return format_response(content, format, title)
        
    except Exception as e:
        error_msg = f"Error fetching troubleshooting info: {str(e)}"
        if format == ResponseFormat.JSON:
            return json.dumps({"error": error_msg})
        return f"❌ {error_msg}"

@mcp.tool(
    description="""Fetch a specific file from the React Native Godot repository.
    
    This tool retrieves any file from the repository, including:
    - Documentation files (README.md, docs/*.md)
    - Example code (example/*.tsx, example/*.ts)
    - Configuration files (package.json, tsconfig.json)
    - Build scripts (*.sh)
    - Native code (ios/*, android/*)
    
    Useful for accessing specific implementation details, examples,
    or configuration that might not be in the main documentation.
    
    Examples:
    - "README.md" - Main documentation
    - "example/App.tsx" - Example app implementation
    - "package.json" - Package configuration
    - "example/export_godot.sh" - Export script"""
)
async def get_file_from_repo(
    context: Context,
    path: str,
    branch: str = DEFAULT_BRANCH,
    format: ResponseFormat = ResponseFormat.MARKDOWN
) -> str:
    """Fetch a specific file from the repository"""
    
    try:
        content = await fetch_file(path, branch)
        
        # Determine file type for syntax highlighting
        file_ext = path.split('.')[-1] if '.' in path else ''
        
        if format == ResponseFormat.MARKDOWN and file_ext in ['ts', 'tsx', 'js', 'jsx', 'json', 'sh', 'gradle', 'xml', 'swift', 'java', 'kt']:
            # Add syntax highlighting
            content = f"```{file_ext}\n{content}\n```"
        
        title = f"File: {path}"
        content = truncate_content(content)
        
        return format_response(content, format, title)
        
    except Exception as e:
        error_msg = f"Error fetching file: {str(e)}"
        if format == ResponseFormat.JSON:
            return json.dumps({"error": error_msg})
        return f"❌ {error_msg}"

# === Main Entry Point ===

def main():
    """Main entry point for the MCP server"""
    mcp.run()

if __name__ == "__main__":
    main()
