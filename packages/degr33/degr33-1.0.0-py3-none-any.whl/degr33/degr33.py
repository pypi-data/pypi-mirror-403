
#!/usr/bin/env python3
"""
what-changed.py

Read-only AI assistant for explaining Linux commands and tools BEFORE execution.
NEVER executes commands. Safe for security environments.
"""

import sys
import os
import argparse
import getpass
from pathlib import Path
import site

# -----------------------------
# Config paths
# -----------------------------
CONFIG_DIR = Path.home() / ".config" / "what-changed"
CONFIG_FILE = CONFIG_DIR / "config"

# -----------------------------
# Utility functions
# -----------------------------
def fatal(msg):
    print(f"ERROR: {msg}")
    sys.exit(1)


def running_on_externally_managed_python():
    """Detect PEP 668 / Kali-protected Python."""
    for p in site.getsitepackages():
        if "EXTERNALLY-MANAGED" in str(p):
            return True
    return os.path.exists("/usr/share/doc/python3.13/README.venv")


def check_openai_dependency():
    try:
        from openai import OpenAI
        return OpenAI
    except ImportError:
        if running_on_externally_managed_python():
            fatal(
                "Python environment is externally managed (PEP 668).\n"
                "This tool must be installed as an application using pipx.\n\n"
                "Administrator action required:\n"
                "  sudo apt install pipx\n"
                "  pipx install .\n\n"
                "Do NOT use pip or virtualenv on Kali."
            )
        else:
            fatal(
                "Required dependency 'openai' is not installed.\n"
                "Ask your system administrator to install it."
            )


def load_api_key():
    """Load or ask for OpenAI API key."""
    if "OPENAI_API_KEY" in os.environ:
        return os.environ["OPENAI_API_KEY"]

    if CONFIG_FILE.exists():
        for line in CONFIG_FILE.read_text().splitlines():
            if line.startswith("OPENAI_API_KEY="):
                return line.split("=", 1)[1].strip()

    print("OpenAI API key not found.")
    print("This tool requires an API key to explain commands safely.")
    print("The key will be stored locally with restricted permissions.\n")

    key = getpass.getpass("Enter OpenAI API key: ").strip()
    if not key:
        fatal("No API key provided.")

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(f"OPENAI_API_KEY={key}\n")
    os.chmod(CONFIG_FILE, 0o600)

    print("API key saved securely.")
    return key


# -----------------------------
# Prompt construction
# -----------------------------
def build_prompt(user_input, mode):
    base_rules = (
        "You are a Linux security expert.\n"
        "NEVER execute or simulate commands.\n"
        "ONLY explain what WOULD happen if executed.\n"
        "Warn clearly if dangerous.\n"
        "Admit uncertainty when behavior depends on environment.\n"
        "Use simple human-readable language.\n"
    )

    if mode == "command":
        return (
            base_rules
            + f"""
Explain the following Linux command:

{user_input}

Explain:
- What it does
- Which system components it may affect
- Security or safety risks
- Environment-dependent behavior
"""
        )

    if mode == "tool":
        return (
            base_rules
            + f"""
Explain the following Linux tool:

{user_input}

Explain:
- What the tool is
- Common use cases
- High-level usage (no execution)
- Security considerations
"""
        )

    if mode == "install":
        return (
            base_rules
            + f"""
Explain installation of the following Linux tool:

{user_input}

Explain:
- What the tool is used for
- How it is installed on Debian/Ubuntu, Arch, Fedora
- Basic setup steps
- Do NOT run commands
"""
        )

    fatal("Invalid mode.")


# -----------------------------
# OpenAI interaction
# -----------------------------
def call_openai(prompt, api_key, OpenAI):
    client = OpenAI(api_key=api_key)
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Cautious Linux security assistant"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=600,
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        fatal("Failed to contact OpenAI service.")


# -----------------------------
# Main CLI
# -----------------------------
def main():
    parser = argparse.ArgumentParser(
        prog="degr33",
        description=(
            "................................................\n"
            " degr33 — Read-only Linux explanation tool\n"
            "................................................\n"
            "Explains Linux commands and tools BEFORE execution.\n"
            "This tool NEVER executes or simulates commands.\n"
            "Designed for security, auditing, and safe learning."
        ),
        epilog=(
            "USAGE EXAMPLES:\n"
            "  Explain a command:\n"
            "    degr33 \"command\"\n\n"
            "  Explain a tool:\n"
            "    degr33 <toolName>\n\n"
            "  Explain tool installation:\n"
            "    degr33 --install <toolName>\n\n"
            "  Show version:\n"
            "    degr33 --version\n"
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument(
        "input",
        nargs="?",
        help="Linux command (quoted) or tool name"
    )

    parser.add_argument(
        "--install",
        metavar="TOOL",
        help="Explain how a Linux tool is installed (no execution)"
    )

    parser.add_argument(
        "-v", "--version",
        action="version",
        version="degr33 1.0.0",
        help="Show tool version"
    )

    args = parser.parse_args()

    if not args.input and not args.install:
        parser.print_help()
        sys.exit(0)

    OpenAI = check_openai_dependency()
    api_key = load_api_key()

    if args.install:
        prompt = build_prompt(args.install, "install")
    elif args.input and " " in args.input:
        prompt = build_prompt(args.input, "command")
    else:
        prompt = build_prompt(args.input, "tool")

    output = call_openai(prompt, api_key, OpenAI)

    print("\n=== READ-ONLY EXPLANATION ===\n")
    print(output)
    print("\n=== END ===\n")


if __name__ == "__main__":
    main()
