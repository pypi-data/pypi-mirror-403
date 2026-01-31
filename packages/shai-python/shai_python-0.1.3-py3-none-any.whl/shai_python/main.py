#!/usr/bin/env python3
"""
Command line tool that generates shell commands based on user input prompts and optionally executes them.
Using DeepSeek model version
"""

import os
import platform
import re
import subprocess
import sys
import threading
import time

from pydantic_ai.agent import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from .config import GREEN, RED, RESET, YELLOW, ConfigManager, ShellCommand


def loading_animation(stop_event: threading.Event, message: str = "Generating command..."):
    """Show a loading animation with the given message"""
    chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
    idx = 0
    print(f"{message}", end="", flush=True)
    while not stop_event.is_set():
        print(f"\r{chars[idx % len(chars)]} {message}", end="", flush=True)
        idx += 1
        time.sleep(0.1)
    # Clear the animation line
    print("\r" + " " * 50 + "\r", end="", flush=True)


def run_with_animation(func, *args, message: str = "Thinking", **kwargs):
    """Run a function with a loading animation"""
    stop_event = threading.Event()
    animation_thread = threading.Thread(target=loading_animation, args=(stop_event, message))
    animation_thread.start()
    
    try:
        result = func(*args, **kwargs)
        stop_event.set()
        animation_thread.join()
        return result
    except Exception as e:
        stop_event.set()
        animation_thread.join()
        raise e


def get_color_for_danger(danger_level: str) -> str:
    """Get color code based on danger level category"""
    if danger_level.lower() == "safe":
        return GREEN
    elif danger_level.lower() == "caution":
        return YELLOW
    else:
        return RED


def format_danger_level(danger_level: str) -> str:
    """Format danger level with color"""
    color = get_color_for_danger(danger_level)
    return f"{color}{danger_level.upper()}{RESET}"


def get_system_info():
    """Get system environment information"""
    system = platform.system()  # Linux, Darwin (macOS), Windows
    release = platform.release()
    shell = os.environ.get("SHELL", "unknown")

    return f"""
Operating System: {system}
System Version: {release}
Shell: {shell}
"""


def execute_shell_command(command: str):
    """Execute shell command"""
    # Safety check: prevent some dangerous operations
    dangerous_patterns = [
        r"rm\s+-rf\s+/",  # Delete root directory
        r"rm\s+-rf\s+\$HOME",  # Delete home directory
        r"rm\s+-rf\s+\*",  # Delete all content in current directory
        r">\s*/dev/sda",  # Direct write to disk device
        r"dd\s+if=",  # Disk write command
        r":\(\)\{\s*:|\s*&\s*\};",  # Fork bomb
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, command):
            print(f"Dangerous command pattern detected: {command}")
            confirm = input(
                "Are you sure you want to execute this dangerous command? (YES/no): "
            )
            if confirm != "YES":
                print("Dangerous command cancelled.")
                return

    try:
        subprocess.run(
            command,
            shell=True,
            check=True,
            text=True,
        )

    except subprocess.CalledProcessError as e:
        print(f"Command execution failed, exit code: {e.returncode}")
        if e.stderr.strip():
            print("Error message:", e.stderr)



def display_shell_command(shell_cmd: ShellCommand):
    """Show shell command with color"""
    # Get color for command based on danger level
    command_color = get_color_for_danger(shell_cmd.risk)

    print(f"\ncmd>> {command_color}{shell_cmd.command}{RESET}")
    print(f"{shell_cmd.explanation}")

    # Decide whether to execute command based on danger level
    if shell_cmd.risk.lower() == "danger":
        response = (
            input(
                f"\nThis command has a risk level of {format_danger_level(shell_cmd.risk)}, still execute? (YES/no): "
            )
            .strip()
            .lower()
        )
        if response != "yes":
            print("Command not executed.")
            return
    else:
        response = input(f"\n[{format_danger_level(shell_cmd.risk)}]Execute this command? (y/N): ").strip().lower()

    if response in ["y", "yes"]:
        execute_shell_command(shell_cmd.command)
    else:
        print("Command not executed.")


def main():
    """Main function"""
    is_init = ConfigManager.ensure_config()
    if is_init:
        edit_command = ConfigManager.get_edit_command()
        display_shell_command(edit_command)
        return

    # Get user prompt from command line arguments or interactive input

    user_prompt = " ".join(sys.argv[1:])
    while not user_prompt:
        user_prompt = input(">> ").strip()

    if user_prompt.lower() == "config":
        edit_command = ConfigManager.get_edit_command()
        display_shell_command(edit_command)
        return

    try:
        config = ConfigManager.load_and_validate()

        target_name = config.default_model
        model_entry = next((m for m in config.models if m.id == target_name or m.alias == target_name), None)
        if not model_entry:
            raise ValueError(f"找不到模型: '{target_name}'")

        provider_info = config.providers.get(model_entry.provider)
        if not provider_info:
            raise ValueError(f"未配置Provider: '{model_entry.provider}'")

        if provider_info.api_key.startswith("$"):
            raise ValueError(f"未定义环境变量: {provider_info.api_key}")

        provider = OpenAIProvider(
            base_url=provider_info.base_url,
            api_key=provider_info.api_key
        )

        model = OpenAIChatModel(model_name=model_entry.id, provider=provider)

         # Create Agent
        agent = Agent(
            model=model,
            output_type=ShellCommand,
            system_prompt=(
                f"You are a professional shell command generation assistant. Based on the user's description, generate accurate shell commands."
                f"Also provide brief command explanations and evaluate the risk level."
                f"Risk levels (low risk: 'safe', harmless commands), 'caution' (medium risk, may have side effects), or 'danger' (high risk, potentially harmful)."
                f"Ensure commands are compatible with the current system environment.\n\n"
                f"Current system environment information:\n{get_system_info()}"
            ),
        )

    except Exception as e:
        print(f"{RED}配置解析失败: {e}{RESET}")
        edit_command = ConfigManager.get_edit_command()
        display_shell_command(edit_command)
        return

    try:
        # Run the agent to get results with animation
        result = run_with_animation(
            agent.run_sync,
            user_prompt,
            message="Thinking..."
        )

        display_shell_command(result.output)

    except Exception as e:
        print(f"Error: {e}")
        exit(1)


if __name__ == "__main__":
    main()
