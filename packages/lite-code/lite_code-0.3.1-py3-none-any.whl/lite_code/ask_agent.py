import os
import json
import time
import logging
from typing import Dict, Any, List, Optional
from cerebras.cloud.sdk import Cerebras

from lite_code.tools import list_files, read_file, read_multiple_files, search_code
from lite_code.utils import extract_json_from_response, check_context_limits

logger = logging.getLogger(__name__)

# Rate limiting config
MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 1.0
MAX_RETRY_DELAY = 30.0

ASK_SYSTEM_PROMPT = """You are an expert code analyst and educator. Your task is to answer questions about code, explain code flow, and generate diagrams when requested.

Available tools:
- list_files: List Python (.py) and JavaScript/TypeScript (.js, .ts) files in directory
- read_file: Read the full content of a file
- read_multiple_files: Read multiple files at once (more efficient than reading one by one)
- search_code: Search for regex patterns across files or in a specific file

Process:
1. Understand the user's question
2. Use tools to explore the codebase if needed
3. IMPORTANT: Use read_multiple_files when you need to read multiple files - it's much more efficient
4. Provide clear, detailed answers
5. Generate diagrams in Mermaid format when requested

Diagram formats:
- Flowcharts: Use Mermaid flowchart syntax
- Sequence diagrams: Use Mermaid sequence diagram syntax
- Class diagrams: Use Mermaid class diagram syntax
- Architecture diagrams: Use Mermaid graph syntax

CRITICAL INSTRUCTIONS:
- You MUST return your final response as valid JSON only
- Do NOT include markdown formatting, explanations, or extra text
- Do NOT use ```json or ``` code blocks
- Return ONLY the JSON object
- Put your detailed answer in the "answer" field

Response format (JSON ONLY):
{
  "status": "complete",
  "answer": "Your detailed answer here",
  "diagram": "Mermaid diagram code (optional)",
  "diagram_type": "flowchart|sequence|class|graph (optional)"
}"""


class AskAgent:
    def __init__(self, api_key: Optional[str] = None, model: str = "zai-glm-4.7"):
        """Initialize the ask agent with Cerebras SDK."""
        self.api_key = api_key or os.getenv("CEREBRAS_API_KEY")
        if not self.api_key:
            raise ValueError("CEREBRAS_API_KEY environment variable not set")
        
        self.model = model
        self.client = Cerebras(api_key=self.api_key)
        self.tools_schema = self._build_tools_schema()
        self.max_iterations = 15
    
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
                                "description": "Optional file extensions to filter"
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
                    "description": "Search for regex patterns across files or in a specific file",
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
                temperature=0.3
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
    
    def ask(self, question: str, context: List[str] = None) -> Dict[str, Any]:
        """Answer a question about the codebase."""
        logger.info(f"Answering question: {question}")
        logger.info(f"Context: {context or 'None'}")

        context_info = ""
        if context:
            limits = check_context_limits(context)
            context_info = f"\nContext files/folders: {', '.join(context)}"
            if limits["total_tokens"] > 0:
                context_info += f"\n(Estimated ~{limits['total_tokens']:,} tokens in {limits['file_count']} files)"
            for warning in limits.get("warnings", []):
                logger.warning(f"Context warning: {warning}")

        messages = [
            {"role": "system", "content": ASK_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"""Question: {question}{context_info}

Please analyze the codebase and provide a detailed answer. Use the available tools to explore files and understand the code structure.

IMPORTANT: Return your final answer as a JSON object only, without markdown formatting."""
            }
        ]

        iteration = 0
        json_parse_failures = 0
        max_json_failures = 3

        while iteration < self.max_iterations:
            iteration += 1
            logger.info(f"Iteration {iteration}/{self.max_iterations}")

            try:
                response = self._call_model(messages)

                if response["content"]:
                    logger.info(f"Model response received")

                if not response["tool_calls"]:
                    logger.info("No tool calls, checking for completion")
                    if response["content"]:
                        # Use improved JSON extraction
                        result, parse_error = extract_json_from_response(response["content"])

                        if result and result.get("status") == "complete":
                            logger.info("Answer complete")
                            return {
                                "status": "success",
                                "answer": result.get("answer", ""),
                                "diagram": result.get("diagram", ""),
                                "diagram_type": result.get("diagram_type", ""),
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
                                    "content": "Please return your response as a valid JSON object only. Format: {\"status\": \"complete\", \"answer\": \"your answer here\"}"
                                })
                                continue
                            else:
                                # Return whatever we got as plain text
                                return {
                                    "status": "success",
                                    "answer": response["content"],
                                    "diagram": "",
                                    "diagram_type": "",
                                    "iterations": iteration,
                                    "note": "Response was not in JSON format"
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

        logger.warning("Max iterations reached")
        return {
            "status": "incomplete",
            "answer": "Could not complete the analysis within the iteration limit.",
            "iterations": iteration
        }
