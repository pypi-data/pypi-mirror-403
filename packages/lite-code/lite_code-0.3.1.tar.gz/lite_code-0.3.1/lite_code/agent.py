import os
import json
import time
import logging
from typing import Dict, Any, List, Optional
from cerebras.cloud.sdk import Cerebras

from lite_code.tools import list_files, read_file, read_multiple_files, search_code, generate_diff
from lite_code.utils import extract_json_from_response, estimate_tokens, check_context_limits

logger = logging.getLogger(__name__)

# Rate limiting config
MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 1.0  # seconds
MAX_RETRY_DELAY = 30.0  # seconds

SYSTEM_PROMPT = """You are an expert code refactoring assistant specializing in Python and JavaScript/TypeScript. Your task is to analyze codebases and perform safe, automated refactoring based on user requirements.

Available tools:
- list_files: List Python (.py) and JavaScript/TypeScript (.js, .ts) files in directory
- read_file: Read the full content of a file
- read_multiple_files: Read multiple files at once (more efficient than reading one by one)
- search_code: Search for regex patterns across files or in a specific file
- generate_diff: Generate unified diff between original and modified code

Process:
1. Analyze the refactoring task
2. Use tools to explore the codebase
3. IMPORTANT: Use read_multiple_files when you need to read multiple files - it's much more efficient
4. Identify files that need changes
5. Generate refactored code
6. Provide diffs for review

CRITICAL INSTRUCTIONS:
- You MUST return your final response as valid JSON only
- Do NOT include markdown formatting, explanations, or extra text
- Do NOT use ```json or ``` code blocks
- Return ONLY the JSON object
- If you need to explain something, put it in the "reasoning" field

Response format when done (JSON ONLY):
{
  "status": "complete",
  "reasoning": "Summary of what was done",
  "changes": {
    "path/to/file1.py": "new content...",
    "path/to/file2.js": "new content..."
  }
}

If you need more information, continue using tools and provide your reasoning."""


class RefactoringAgent:
    def __init__(self, api_key: Optional[str] = None, model: str = "zai-glm-4.7"):
        """Initialize the refactoring agent with Cerebras SDK."""
        self.api_key = api_key or os.getenv("CEREBRAS_API_KEY")
        if not self.api_key:
            raise ValueError("CEREBRAS_API_KEY environment variable not set")
        
        self.model = model
        self.client = Cerebras(api_key=self.api_key)
        self.tools_schema = self._build_tools_schema()
        self.max_iterations = 20
        self.conversation_history = []
    
    def _build_tools_schema(self) -> List[Dict[str, Any]]:
        """Build tool schema for function calling."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "list_files",
                    "description": "List Python (.py) and JavaScript/TypeScript (.js, .ts) files in directory",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "root_path": {
                                "type": "string",
                                "description": "Root directory path to search"
                            },
                            "extensions": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Optional file extensions to filter (e.g., ['.py', '.js'])"
                            }
                        },
                        "required": ["root_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Read the full content of a single file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the file to read"
                            }
                        },
                        "required": ["file_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "read_multiple_files",
                    "description": "Read multiple files at once - much more efficient than reading one by one. Use this when you need to read multiple files.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_paths": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of file paths to read"
                            }
                        },
                        "required": ["file_paths"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_code",
                    "description": "Search for regex pattern across files or in a specific file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pattern": {
                                "type": "string",
                                "description": "Regex pattern to search for"
                            },
                            "file_path": {
                                "type": "string",
                                "description": "Optional specific file path to search in"
                            }
                        },
                        "required": ["pattern"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_diff",
                    "description": "Generate unified diff between original and modified code",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "original_content": {
                                "type": "string",
                                "description": "Original file content"
                            },
                            "modified_content": {
                                "type": "string",
                                "description": "Modified file content"
                            }
                        },
                        "required": ["original_content", "modified_content"]
                    }
                }
            }
        ]
    
    def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool and return its result."""
        try:
            if tool_name == "list_files":
                return list_files(
                    arguments["root_path"],
                    arguments.get("extensions")
                )
            elif tool_name == "read_file":
                return read_file(arguments["file_path"])
            elif tool_name == "read_multiple_files":
                return read_multiple_files(arguments["file_paths"])
            elif tool_name == "search_code":
                return search_code(
                    arguments["pattern"],
                    arguments.get("file_path")
                )
            elif tool_name == "generate_diff":
                return generate_diff(
                    arguments["original_content"],
                    arguments["modified_content"]
                )
            else:
                return {"error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return {"error": str(e)}
    
    def _call_model(self, messages: List[Dict[str, str]], retry_count: int = 0) -> Dict[str, Any]:
        """Call model via Cerebras with retry logic for rate limits."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.tools_schema,
                tool_choice="auto",
                temperature=0.1
            )

            message = response.choices[0].message
            result = {
                "content": message.content,
                "tool_calls": message.tool_calls
            }

            return result

        except Exception as e:
            error_str = str(e).lower()

            # Check for rate limit or transient errors
            is_rate_limit = "rate" in error_str or "429" in error_str or "limit" in error_str
            is_transient = "timeout" in error_str or "connection" in error_str or "503" in error_str

            if (is_rate_limit or is_transient) and retry_count < MAX_RETRIES:
                delay = min(INITIAL_RETRY_DELAY * (2 ** retry_count), MAX_RETRY_DELAY)
                logger.warning(f"API error (attempt {retry_count + 1}/{MAX_RETRIES}), retrying in {delay}s: {e}")
                time.sleep(delay)
                return self._call_model(messages, retry_count + 1)

            logger.error(f"Error calling model: {e}")
            raise
    
    def refactor(self, task: str, context: List[str] = None) -> Dict[str, Any]:
        """Execute refactoring task with context using batch processing."""
        logger.info(f"Starting refactoring: {task}")
        logger.info(f"Context: {context or 'None'}")

        if not context:
            return {
                "status": "error",
                "error": "No context provided",
                "iterations": 0
            }

        # Check context limits
        limits = check_context_limits(context)
        if limits["warnings"]:
            for warning in limits["warnings"]:
                logger.warning(f"Context warning: {warning}")

        context_info = f"\nContext files/folders: {', '.join(context)}"
        if limits["total_tokens"] > 0:
            context_info += f"\n(Estimated ~{limits['total_tokens']:,} tokens in {limits['file_count']} files)"

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"""Refactoring task: {task}{context_info}

Please analyze the codebase and perform the requested refactoring. Use the available tools to explore files, understand the code structure, and generate the refactored code.

IMPORTANT: When you're done, return a JSON object with status="complete", reasoning, and changes. Do not wrap in markdown."""
            }
        ]

        iteration = 0
        tool_results = []
        json_parse_failures = 0
        max_json_failures = 3

        while iteration < self.max_iterations:
            iteration += 1
            logger.info(f"Iteration {iteration}/{self.max_iterations}")

            try:
                response = self._call_model(messages)

                if response["content"]:
                    logger.info(f"Model reasoning: {response['content'][:200]}...")

                if not response["tool_calls"]:
                    logger.info("No tool calls, checking for completion")
                    if response["content"]:
                        # Use improved JSON extraction
                        result, parse_error = extract_json_from_response(response["content"])

                        if result and result.get("status") == "complete":
                            logger.info("Refactoring complete")
                            return {
                                "status": "success",
                                "reasoning": result.get("reasoning", ""),
                                "changes": result.get("changes", {}),
                                "iterations": iteration
                            }
                        elif parse_error:
                            json_parse_failures += 1
                            logger.warning(f"JSON parse attempt {json_parse_failures}/{max_json_failures}: {parse_error}")

                            if json_parse_failures < max_json_failures:
                                # Ask model to return proper JSON
                                messages.append({
                                    "role": "assistant",
                                    "content": response["content"]
                                })
                                messages.append({
                                    "role": "user",
                                    "content": "Please return your response as a valid JSON object only, without markdown formatting. Format: {\"status\": \"complete\", \"reasoning\": \"...\", \"changes\": {...}}"
                                })
                                continue
                            else:
                                logger.error("Max JSON parse failures reached")
                                # Try to salvage any changes mentioned
                                return {
                                    "status": "incomplete",
                                    "reasoning": "Could not parse model response as JSON",
                                    "raw_response": response["content"][:2000],
                                    "iterations": iteration
                                }

                    break

                for tool_call in response["tool_calls"]:
                    tool_name = tool_call.function.name
                    try:
                        arguments = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        logger.error(f"Invalid arguments for {tool_name}")
                        continue

                    logger.info(f"Calling tool: {tool_name}")
                    result = self._execute_tool(tool_name, arguments)
                    tool_results.append({
                        "tool": tool_name,
                        "arguments": arguments,
                        "result": result
                    })

                    messages.append({
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [tool_call]
                    })

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result)
                    })

            except Exception as e:
                logger.error(f"Error in iteration {iteration}: {e}")
                return {
                    "status": "error",
                    "error": str(e),
                    "iterations": iteration
                }

        logger.warning("Max iterations reached without completion")
        return {
            "status": "incomplete",
            "reasoning": "Max iterations reached",
            "tool_results": tool_results,
            "iterations": iteration
        }
