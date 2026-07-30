import argparse
import json
import os
import subprocess
import sys

from dotenv import load_dotenv
import anthropic
from openai import OpenAI

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", default="https://openrouter.ai/api/v1")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_BASE_URL = os.getenv("GEMINI_BASE_URL", default="https://generativelanguage.googleapis.com/v1beta/openai/")

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read and return the contents of a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "The path to the file to read",
                    }
                },
                "required": ["file_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "Write",
            "description": "Write content to a file",
            "parameters": {
                "type": "object",
                "required": ["file_path", "content"],
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "The path of the file to write to",
                    },
                    "content": {
                        "type": "string",
                        "description": "The content to write to the file",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "Bash",
            "description": "Execute a shell command",
            "parameters": {
                "type": "object",
                "required": ["command"],
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The command to execute",
                    }
                },
            },
        },
    },
]


def get_anthropic_tools():
    return [
        {
            "name": tool["function"]["name"],
            "description": tool["function"]["description"],
            "input_schema": tool["function"]["parameters"],
        }
        for tool in TOOLS
    ]


def execute_tool(name, arguments):
    if name == "read_file":
        file_path = arguments["file_path"]
        with open(file_path, "r") as f:
            return f.read()
    elif name == "Write":
        file_path = arguments["file_path"]
        content = arguments["content"]
        with open(file_path, "w") as f:
            f.write(content)
        return "File written successfully"
    elif name == "Bash":
        command = arguments["command"]
        if command.strip().startswith("cd"):
            return "Change directory command not allowed"
        elif command.strip() == "":
            return "Empty command not allowed"
        else:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True
            )
            return result.stdout + result.stderr
    return f"Unknown tool: {name}"


def run_openai_provider(api_key, base_url, model, prompt, provider_name="OpenAI"):
    if not api_key or api_key.startswith("your_"):
        raise RuntimeError(f"{provider_name}_API_KEY is missing or invalid")

    client = OpenAI(api_key=api_key, base_url=base_url)
    messages = [{"role": "user", "content": prompt}]

    while True:
        chat = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=TOOLS,
        )

        if not chat.choices:
            raise RuntimeError("no choices in response")

        response_message = chat.choices[0].message
        messages.append(response_message)

        tool_calls = response_message.tool_calls
        if tool_calls:
            for tool_call in tool_calls:
                arguments = json.loads(tool_call.function.arguments)
                tool_result = execute_tool(tool_call.function.name, arguments)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_result,
                    }
                )
        else:
            if response_message.content:
                print(response_message.content)
            break


def run_openrouter(prompt):
    run_openai_provider(
        api_key=OPENROUTER_API_KEY,
        base_url=OPENROUTER_BASE_URL,
        model="anthropic/claude-haiku-4.5",
        prompt=prompt,
        provider_name="OPENROUTER",
    )


def run_gemini(prompt):
    run_openai_provider(
        api_key=GEMINI_API_KEY,
        base_url=GEMINI_BASE_URL,
        model="gemini-3.6-flash",
        prompt=prompt,
        provider_name="GEMINI",
    )


def run_anthropic_direct(prompt):
    if not ANTHROPIC_API_KEY or ANTHROPIC_API_KEY.startswith("your_"):
        raise RuntimeError("ANTHROPIC_API_KEY is missing or invalid")

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    messages = [{"role": "user", "content": prompt}]

    while True:
        response = client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=4096,
            messages=messages,
            tools=get_anthropic_tools(),
        )
        messages.append({"role": "assistant", "content": response.content})

        tool_use_blocks = [block for block in response.content if block.type == "tool_use"]
        if tool_use_blocks:
            tool_results = []
            for block in tool_use_blocks:
                res_text = execute_tool(block.name, block.input)
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": res_text,
                    }
                )
            messages.append({"role": "user", "content": tool_results})
        else:
            for block in response.content:
                if block.type == "text":
                    print(block.text)
            break


def main():
    p = argparse.ArgumentParser()
    p.add_argument("-p", required=True)
    args = p.parse_args()

    providers = [
        ("OpenRouter", run_openrouter),
        ("Anthropic", run_anthropic_direct),
        ("Gemini", run_gemini),
    ]

    for name, provider_fn in providers:
        try:
            print(f"[Info] Attempting with {name} API...", file=sys.stderr)
            provider_fn(args.p)
            return
        except Exception as e:
            print(f"[Warning] {name} provider failed: {e}", file=sys.stderr)

    print("[Error] All API providers failed. Please check your API keys in .env", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
