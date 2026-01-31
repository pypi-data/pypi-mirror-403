"""
Verlex CLI - Command-line interface for Verlex cloud execution.

A minimal CLI that talks to the Verlex API.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Optional

# Optional rich import for pretty output
try:
    from rich.console import Console
    from rich.table import Table
    console = Console()
    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    console = None


def print_msg(msg: str, style: str = None):
    """Print a message, using rich if available."""
    if HAS_RICH and console:
        if style:
            console.print(f"[{style}]{msg}[/{style}]")
        else:
            console.print(msg)
    else:
        print(msg)


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        prog="verlex",
        description="Verlex - Run your code in the cloud for the price of a coffee",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  verlex login                    # Store API key
  verlex run script.py            # Run a script in the cloud
  verlex run script.py --gpu A100 # Run with specific GPU
  verlex jobs                     # List recent jobs
  verlex whoami                   # Show authenticated user

Get your API key at: https://verlex.dev
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Login command
    login_parser = subparsers.add_parser("login", help="Store API key")
    login_parser.add_argument("--api-key", "-k", help="API key")

    # Logout command
    subparsers.add_parser("logout", help="Clear stored credentials")

    # Whoami command
    subparsers.add_parser("whoami", help="Show current authenticated user")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run a script in the cloud")
    run_parser.add_argument("script", help="Python script to run")
    run_parser.add_argument("--priority", action="store_true", default=True,
                           help="Priority mode: immediate execution (default)")
    run_parser.add_argument("--patient", dest="priority", action="store_false",
                           help="Patient mode: wait for lower price")
    run_parser.add_argument("--gpu", "-g", help="GPU type (T4, A10, A100, H100, L4)")
    run_parser.add_argument("--cpu", "-c", type=int, help="CPU cores")
    run_parser.add_argument("--memory", "-m", help="Memory (e.g., 8GB, 16GB)")
    run_parser.add_argument("--timeout", "-t", type=int, default=3600, help="Timeout in seconds")

    # Jobs command
    jobs_parser = subparsers.add_parser("jobs", help="List recent jobs")
    jobs_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # Status command
    status_parser = subparsers.add_parser("status", help="Check job status")
    status_parser.add_argument("job_id", help="Job ID")

    # Logs command
    logs_parser = subparsers.add_parser("logs", help="View job logs")
    logs_parser.add_argument("job_id", help="Job ID")
    logs_parser.add_argument("--follow", "-f", action="store_true", help="Follow logs")

    # Version command
    subparsers.add_parser("version", help="Show version information")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 0

    try:
        if args.command == "login":
            return cmd_login(args)
        elif args.command == "logout":
            return cmd_logout(args)
        elif args.command == "whoami":
            return cmd_whoami(args)
        elif args.command == "run":
            return cmd_run(args)
        elif args.command == "jobs":
            return cmd_jobs(args)
        elif args.command == "status":
            return cmd_status(args)
        elif args.command == "logs":
            return cmd_logs(args)
        elif args.command == "version":
            return cmd_version(args)
        else:
            parser.print_help()
            return 1
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        return 130
    except Exception as e:
        print_msg(f"Error: {e}", "red")
        return 1


def get_api_key() -> Optional[str]:
    """Get API key from environment or config file."""
    # Check environment variable
    api_key = os.getenv("VERLEX_API_KEY")
    if api_key:
        return api_key

    # Check config file
    config_path = Path.home() / ".verlex" / "config.json"
    if config_path.exists():
        try:
            with open(config_path) as f:
                config = json.load(f)
                return config.get("api_key")
        except Exception:
            pass

    return None


def save_api_key(api_key: str) -> None:
    """Save API key to config file."""
    config_dir = Path.home() / ".verlex"
    config_dir.mkdir(exist_ok=True)

    config_path = config_dir / "config.json"
    config = {}

    if config_path.exists():
        try:
            with open(config_path) as f:
                config = json.load(f)
        except Exception:
            pass

    config["api_key"] = api_key

    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    # Set restrictive permissions
    config_path.chmod(0o600)


def cmd_login(args) -> int:
    """Handle login command."""
    import httpx

    api_key = args.api_key

    if not api_key:
        # Prompt for API key
        print("Enter your Verlex API key (get one at https://verlex.dev):")
        api_key = input("> ").strip()

    if not api_key:
        print_msg("No API key provided.", "red")
        return 1

    # Validate key
    api_url = os.getenv("VERLEX_API_URL", "https://api.verlex.dev")

    try:
        response = httpx.get(
            f"{api_url}/v1/auth/me",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10.0,
        )

        if response.status_code == 200:
            save_api_key(api_key)
            data = response.json()
            print_msg(f"Logged in as: {data.get('email', 'user')}", "green")
            return 0
        elif response.status_code == 401:
            print_msg("Invalid API key.", "red")
            return 1
        else:
            print_msg(f"Login failed: {response.text}", "red")
            return 1
    except httpx.RequestError as e:
        print_msg(f"Network error: {e}", "red")
        return 1


def cmd_logout(args) -> int:
    """Handle logout command."""
    config_path = Path.home() / ".verlex" / "config.json"

    if config_path.exists():
        try:
            with open(config_path) as f:
                config = json.load(f)
            config.pop("api_key", None)
            with open(config_path, "w") as f:
                json.dump(config, f, indent=2)
        except Exception:
            pass

    print_msg("Logged out.", "green")
    return 0


def cmd_whoami(args) -> int:
    """Handle whoami command."""
    import httpx

    api_key = get_api_key()
    if not api_key:
        print_msg("Not logged in. Run 'verlex login' first.", "yellow")
        return 1

    api_url = os.getenv("VERLEX_API_URL", "https://api.verlex.dev")

    try:
        response = httpx.get(
            f"{api_url}/v1/auth/me",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10.0,
        )

        if response.status_code == 200:
            data = response.json()
            print(f"Email: {data.get('email', 'N/A')}")
            print(f"Tier:  {data.get('tier', 'free')}")
            print(f"Credits: ${data.get('credits', 0):.2f}")
            return 0
        else:
            print_msg("Failed to get user info.", "red")
            return 1
    except httpx.RequestError as e:
        print_msg(f"Network error: {e}", "red")
        return 1


def cmd_run(args) -> int:
    """Handle run command."""
    from verlex import GateWay, NotAuthenticatedError

    api_key = get_api_key()
    if not api_key:
        print_msg("Not logged in. Run 'verlex login' first.", "yellow")
        return 1

    script_path = Path(args.script)
    if not script_path.exists():
        print_msg(f"Script not found: {args.script}", "red")
        return 1

    # Read script
    with open(script_path) as f:
        script_code = f.read()

    # Create execution function
    def execute_script():
        exec(script_code, {"__name__": "__main__"})

    # Run in cloud
    try:
        with GateWay(
            api_key=api_key,
            priority=args.priority,
            timeout=args.timeout,
        ) as gw:
            result = gw.run(
                execute_script,
                gpu=args.gpu,
                cpu=args.cpu,
                memory=args.memory,
            )

            if result is not None:
                print(f"\nResult: {result}")

            return 0

    except NotAuthenticatedError:
        print_msg("Invalid API key. Run 'verlex login' to re-authenticate.", "red")
        return 1
    except Exception as e:
        print_msg(f"Execution failed: {e}", "red")
        return 1


def cmd_jobs(args) -> int:
    """Handle jobs command."""
    import httpx

    api_key = get_api_key()
    if not api_key:
        print_msg("Not logged in. Run 'verlex login' first.", "yellow")
        return 1

    api_url = os.getenv("VERLEX_API_URL", "https://api.verlex.dev")

    try:
        response = httpx.get(
            f"{api_url}/v1/jobs",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10.0,
        )

        if response.status_code != 200:
            print_msg(f"Failed to get jobs: {response.text}", "red")
            return 1

        jobs = response.json().get("jobs", [])

        if args.json:
            print(json.dumps(jobs, indent=2))
            return 0

        if not jobs:
            print("No jobs found.")
            return 0

        print("\nRecent Jobs")
        print("=" * 60)
        print(f"{'JOB ID':<24} {'STATUS':<12} {'COST':<10}")
        print("-" * 60)

        for job in jobs[:20]:
            cost = job.get("cost", 0)
            cost_str = f"${cost:.4f}" if cost else "-"
            print(f"{job['id'][:22]:<24} {job['status']:<12} {cost_str:<10}")

        print()
        return 0

    except httpx.RequestError as e:
        print_msg(f"Network error: {e}", "red")
        return 1


def cmd_status(args) -> int:
    """Handle status command."""
    import httpx

    api_key = get_api_key()
    if not api_key:
        print_msg("Not logged in. Run 'verlex login' first.", "yellow")
        return 1

    api_url = os.getenv("VERLEX_API_URL", "https://api.verlex.dev")

    try:
        response = httpx.get(
            f"{api_url}/v1/jobs/{args.job_id}/status",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10.0,
        )

        if response.status_code == 404:
            print_msg(f"Job not found: {args.job_id}", "red")
            return 1
        elif response.status_code != 200:
            print_msg(f"Failed to get status: {response.text}", "red")
            return 1

        data = response.json()
        print(f"Job ID:   {args.job_id}")
        print(f"Status:   {data.get('status', 'unknown')}")
        if data.get("provider"):
            print(f"Provider: {data['provider']}")
        if data.get("cost"):
            print(f"Cost:     ${data['cost']:.4f}")

        return 0

    except httpx.RequestError as e:
        print_msg(f"Network error: {e}", "red")
        return 1


def cmd_logs(args) -> int:
    """Handle logs command."""
    import httpx
    import time

    api_key = get_api_key()
    if not api_key:
        print_msg("Not logged in. Run 'verlex login' first.", "yellow")
        return 1

    api_url = os.getenv("VERLEX_API_URL", "https://api.verlex.dev")

    def fetch_logs(offset: int = 0):
        response = httpx.get(
            f"{api_url}/v1/jobs/{args.job_id}/output",
            headers={"Authorization": f"Bearer {api_key}"},
            params={"offset": offset},
            timeout=10.0,
        )
        return response

    try:
        response = fetch_logs()

        if response.status_code == 404:
            print_msg(f"Job not found: {args.job_id}", "red")
            return 1
        elif response.status_code != 200:
            print_msg(f"Failed to get logs: {response.text}", "red")
            return 1

        data = response.json()
        entries = data.get("entries", [])

        for entry in entries:
            content = entry.get("content", entry.get("text", ""))
            print(content, end="")

        if args.follow:
            print("\n--- Following logs (Ctrl+C to stop) ---\n")
            last_index = data.get("current_index", 0)

            while True:
                time.sleep(1)
                response = fetch_logs(last_index)

                if response.status_code == 200:
                    data = response.json()
                    entries = data.get("entries", [])

                    for entry in entries:
                        content = entry.get("content", entry.get("text", ""))
                        print(content, end="")

                    if entries:
                        last_index = data.get("current_index", last_index)

                    if data.get("is_complete"):
                        print("\n--- Job completed ---")
                        break

        return 0

    except httpx.RequestError as e:
        print_msg(f"Network error: {e}", "red")
        return 1


def cmd_version(args) -> int:
    """Handle version command."""
    from verlex import __version__

    print(f"Verlex CLI v{__version__}")
    print(f"Python {sys.version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
