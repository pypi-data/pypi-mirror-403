"""
Starvex CLI - Command Line Interface

The main entry point for the starvex command.
"""

import asyncio
import argparse
import sys
import json
import os
from typing import Optional

from .core import Starvex
from .models import GuardConfig, GuardRule, GuardRuleType
from .utils import generate_api_key, validate_api_key_format, save_api_key, load_api_key

# ASCII art banner
BANNER = """
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   ███████╗████████╗ █████╗ ██████╗ ██╗   ██╗███████╗██╗  ██╗  ║
║   ██╔════╝╚══██╔══╝██╔══██╗██╔══██╗██║   ██║██╔════╝╚██╗██╔╝  ║
║   ███████╗   ██║   ███████║██████╔╝██║   ██║█████╗   ╚███╔╝   ║
║   ╚════██║   ██║   ██╔══██║██╔══██╗╚██╗ ██╔╝██╔══╝   ██╔██╗   ║
║   ███████║   ██║   ██║  ██║██║  ██║ ╚████╔╝ ███████╗██╔╝ ██╗  ║
║   ╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚══════╝╚═╝  ╚═╝  ║
║                                                               ║
║   Production-ready AI agents with guardrails & observability  ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
"""


def print_banner():
    """Print the Starvex banner"""
    print("\033[95m" + BANNER + "\033[0m")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        prog="starvex",
        description="Starvex - Production-ready AI agents with guardrails & observability",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Login command
    login_parser = subparsers.add_parser("login", help="Login with your API key")
    login_parser.add_argument("--key", "-k", help="API key (or enter interactively)")

    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize Starvex in current project")

    # Check command
    check_parser = subparsers.add_parser("check", help="Check a prompt for safety")
    check_parser.add_argument("prompt", help="Prompt to check")
    check_parser.add_argument("--api-key", "-k", help="Starvex API key")
    check_parser.add_argument("--no-trace", action="store_true", help="Disable tracing")

    # Test command
    test_parser = subparsers.add_parser("test", help="Test a prompt/response pair")
    test_parser.add_argument("--prompt", "-p", required=True, help="Test prompt")
    test_parser.add_argument("--response", "-r", required=True, help="Test response")
    test_parser.add_argument("--context", "-c", help="Context (JSON array)")

    # Generate key command (for testing only)
    keygen_parser = subparsers.add_parser("keygen", help="Generate a test API key (dev only)")
    keygen_parser.add_argument("--prefix", default="sv_test_", help="Key prefix")

    # Validate key command
    validate_parser = subparsers.add_parser("validate", help="Validate an API key format")
    validate_parser.add_argument("key", help="API key to validate")

    # Version command
    subparsers.add_parser("version", help="Show version")

    # Config command
    config_parser = subparsers.add_parser("config", help="Show/set configuration")
    config_parser.add_argument("--show", action="store_true", help="Show current config")

    # Status command
    subparsers.add_parser("status", help="Check connection status")

    # Whoami command
    subparsers.add_parser("whoami", help="Show current logged in project")

    # Logout command
    subparsers.add_parser("logout", help="Remove saved API key")

    args = parser.parse_args()

    if args.command == "login":
        run_login(args)
    elif args.command == "init":
        run_init(args)
    elif args.command == "check":
        run_check(args)
    elif args.command == "test":
        run_test(args)
    elif args.command == "keygen":
        run_keygen(args)
    elif args.command == "validate":
        run_validate(args)
    elif args.command == "version":
        run_version()
    elif args.command == "config":
        run_config(args)
    elif args.command == "status":
        run_status()
    elif args.command == "whoami":
        run_whoami()
    elif args.command == "logout":
        run_logout()
    else:
        print_banner()
        parser.print_help()
        print("\n" + "=" * 60)
        print("  Quick Start:")
        print("=" * 60)
        print("\n  1. Get your API key at: https://starvex.in/dashboard")
        print("  2. Run: starvex login")
        print("  3. Start securing your AI agents!")
        print("\n  Example usage in Python:")
        print("  ─────────────────────────")
        print("  from starvex import Starvex")
        print("  ")
        print("  vex = Starvex()")
        print("  result = await vex.protect('user input')")
        print("\n")


def run_login(args):
    """Login with API key"""
    print_banner()

    api_key = args.key

    if not api_key:
        print("\n  Welcome to Starvex!")
        print("  ────────────────────")
        print("\n  Get your API key at: \033[94mhttps://starvex.in/dashboard\033[0m")
        print()
        api_key = input("  Enter your API key: ").strip()

    if not api_key:
        print("\n  ❌ No API key provided.")
        sys.exit(1)

    if not validate_api_key_format(api_key):
        print("\n  ❌ Invalid API key format.")
        print("     Expected: sv_live_xxx or sv_test_xxx")
        sys.exit(1)

    # Validate with server
    print("\n  Validating API key...")

    try:
        import httpx

        response = httpx.post(
            "https://decqadhkqnacujoyirkh.supabase.co/functions/v1/validate-key",
            json={"api_key": api_key},
            timeout=10.0,
        )
        data = response.json()

        if data.get("valid"):
            save_api_key(api_key)
            project = data.get("project", {})
            print(f"\n  ✅ Successfully logged in!")
            print(f"     Project: {project.get('name', 'Unknown')}")
            print(
                f"     Usage: {data.get('usage', {}).get('count', 0)} / {data.get('usage', {}).get('limit', 10000)} requests"
            )
            print("\n  You're ready to start securing your AI agents!")
            print("\n  Example:")
            print("  ─────────")
            print("  from starvex import Starvex")
            print("  vex = Starvex()")
            print("  result = await vex.protect('user input')")
            print()
        else:
            print(f"\n  ❌ Invalid API key: {data.get('error', 'Unknown error')}")
            sys.exit(1)
    except Exception as e:
        # If validation fails, still save the key but warn
        print(f"\n  ⚠️  Could not validate key (server may be unavailable)")
        print(f"     Error: {e}")
        save_api_key(api_key)
        print(f"\n  API key saved. Will validate on first request.")


def run_init(args):
    """Initialize Starvex in current project"""
    print_banner()

    api_key = load_api_key()

    if not api_key:
        print("\n  ❌ Not logged in. Run 'starvex login' first.")
        print("     Get your API key at: https://starvex.in/dashboard")
        sys.exit(1)

    # Create .env example
    env_content = f"""# Starvex Configuration
STARVEX_API_KEY={api_key}
"""

    with open(".env.starvex", "w") as f:
        f.write(env_content)

    print("\n  ✅ Starvex initialized!")
    print("     Created: .env.starvex")
    print("\n  Quick start:")
    print("  ─────────────")
    print("  from starvex import Starvex")
    print("  ")
    print("  vex = Starvex()")
    print("  ")
    print("  async def my_agent(prompt):")
    print("      return 'response'")
    print("  ")
    print("  result = await vex.secure('input', my_agent)")
    print()


def run_check(args):
    """Run prompt safety check"""
    api_key = args.api_key or load_api_key()

    if not api_key:
        print("\n❌ No API key found. Run 'starvex login' first.")
        print("   Get your API key at: https://starvex.in/dashboard")
        sys.exit(1)

    vex = Starvex(api_key=api_key, enable_tracing=not args.no_trace)

    async def run_protect():
        result = await vex.protect(args.prompt)
        return result

    result = asyncio.run(run_protect())

    print(f"\n{'=' * 50}")
    print(f"Starvex Safety Check")
    print(f"{'=' * 50}")
    print(f"Status: {result.status.upper()}")
    print(f"Verdict: {result.verdict.value}")
    print(f"Latency: {result.latency_ms:.2f}ms")
    print(f"Trace ID: {result.trace_id}")

    if result.checks:
        print(f"\nChecks:")
        for check_result in result.checks:
            status_icon = "✅" if check_result.passed else "❌"
            print(f"  {status_icon} {check_result.rule_type.value}: {check_result.confidence:.2f}")
            if check_result.message:
                print(f"     {check_result.message}")

    if result.response:
        print(f"\nMessage: {result.response}")

    print(f"{'=' * 50}\n")

    vex.shutdown()

    if result.status == "blocked":
        sys.exit(1)


def run_test(args):
    """Run prompt/response test"""
    vex = Starvex(enable_tracing=False)

    context = None
    if args.context:
        try:
            context = json.loads(args.context)
        except json.JSONDecodeError:
            print("Error: Context must be valid JSON array")
            sys.exit(1)

    result = vex.test(args.prompt, args.response, context)

    print(f"\n{'=' * 50}")
    print(f"Starvex Test Results")
    print(f"{'=' * 50}")
    print(f"Status: {result.status.upper()}")
    print(f"Verdict: {result.verdict.value}")
    print(f"Latency: {result.latency_ms:.2f}ms")

    if result.checks:
        print(f"\nEvaluation Results:")
        for check_result in result.checks:
            status_icon = "✅" if check_result.passed else "❌"
            print(f"  {status_icon} {check_result.rule_type.value}")
            if check_result.message:
                print(f"     {check_result.message}")

    if result.metadata and "metrics" in result.metadata:
        print(f"\nDetailed Metrics:")
        metrics = result.metadata["metrics"]
        for key, value in metrics.items():
            print(f"  {key}: {value:.3f}")

    print(f"{'=' * 50}\n")

    vex.shutdown()


def run_keygen(args):
    """Generate new test API key"""
    key = generate_api_key(args.prefix)
    print(f"\nGenerated Test API Key:")
    print(f"  {key}")
    print(f"\n⚠️  This is a local test key. For production, get a key at:")
    print(f"   https://starvex.in/dashboard\n")


def run_validate(args):
    """Validate API key format"""
    is_valid = validate_api_key_format(args.key)

    if is_valid:
        print(f"✅ API key format is valid")
        sys.exit(0)
    else:
        print(f"❌ API key format is invalid")
        print(f"   Expected: sv_live_xxx or sv_test_xxx")
        sys.exit(1)


def run_version():
    """Show version"""
    print("Starvex SDK v1.0.0")
    print("https://starvex.in")


def run_config(args):
    """Show configuration"""
    api_key = load_api_key()

    print(f"\n{'=' * 50}")
    print(f"Starvex Configuration")
    print(f"{'=' * 50}")

    if api_key:
        masked_key = f"{api_key[:12]}..." if len(api_key) > 12 else "***"
        print(f"  API Key: {masked_key}")
    else:
        print(f"  API Key: Not configured")

    print(f"  API Host: https://decqadhkqnacujoyirkh.supabase.co/functions/v1")
    print(f"  Dashboard: https://starvex.in/dashboard")
    print(f"{'=' * 50}\n")


def run_status():
    """Check connection status"""
    api_key = load_api_key()

    print("\nStarvex Status")
    print("──────────────")

    if not api_key:
        print("  API Key: ❌ Not configured")
        print("\n  Run 'starvex login' to get started.")
        return

    print(f"  API Key: ✅ Configured")

    try:
        import httpx

        response = httpx.post(
            "https://decqadhkqnacujoyirkh.supabase.co/functions/v1/validate-key",
            json={"api_key": api_key},
            timeout=10.0,
        )
        data = response.json()

        if data.get("valid"):
            print(f"  Connection: ✅ Connected")
            project = data.get("project", {})
            print(f"  Project: {project.get('name', 'Unknown')}")
            usage = data.get("usage", {})
            print(f"  Usage: {usage.get('count', 0)} / {usage.get('limit', 10000)} requests")
        else:
            print(f"  Connection: ❌ Invalid API key")
    except Exception as e:
        print(f"  Connection: ⚠️  Could not connect ({e})")

    print()


def run_whoami():
    """Show current logged in project"""
    api_key = load_api_key()

    if not api_key:
        print("\n❌ Not logged in. Run 'starvex login' first.")
        return

    try:
        import httpx

        response = httpx.post(
            "https://decqadhkqnacujoyirkh.supabase.co/functions/v1/validate-key",
            json={"api_key": api_key},
            timeout=10.0,
        )
        data = response.json()

        if data.get("valid"):
            project = data.get("project", {})
            print(f"\nLogged in as:")
            print(f"  Project: {project.get('name', 'Unknown')}")
            print(f"  Key: {data.get('key_name', 'Default Key')}")
            usage = data.get("usage", {})
            print(f"  Usage: {usage.get('count', 0)} / {usage.get('limit', 10000)} requests")
            print(f"\n  Dashboard: https://starvex.in/dashboard")
        else:
            print(f"\n❌ API key is no longer valid: {data.get('error')}")
    except Exception as e:
        print(f"\n⚠️  Could not verify: {e}")

    print()


def run_logout():
    """Remove saved API key"""
    from .utils import get_config_path

    config_path = get_config_path()

    if os.path.exists(config_path):
        os.remove(config_path)
        print("\n✅ Logged out successfully.")
    else:
        print("\nNo saved credentials found.")

    print()


if __name__ == "__main__":
    main()
