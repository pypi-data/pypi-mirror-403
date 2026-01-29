#!/usr/bin/env python3
"""
Credential Management CLI for LOOVE AI Agent Infrastructure.

This CLI provides tools for setting up, verifying, and managing credentials
for AI assistants (Devin, Manus, Claude Code, etc.) in the LOOVE ecosystem.

Usage:
    python -m integration_validation.credential.cli setup
    python -m integration_validation.credential.cli verify
    python -m integration_validation.credential.cli status
    python -m integration_validation.credential.cli test-github
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any

from .env_credential_manager import EnvCredentialManager
from .github_app_auth import GitHubAppAuth, get_github_app_auth, HAS_JWT, HAS_REQUESTS


def get_credential_store_path() -> Path:
    """Get the credential store path from environment or default."""
    env_path = os.environ.get("LOOVE_CREDENTIAL_STORE_PATH")
    if env_path:
        return Path(os.path.expanduser(env_path))
    return Path.home() / "repos" / "Devin_integrations" / ".env"


def print_header(title: str) -> None:
    """Print a formatted header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")


def print_status(label: str, status: bool, details: str = "") -> None:
    """Print a status line with checkmark or X."""
    icon = "[OK]" if status else "[FAIL]"
    detail_str = f" - {details}" if details else ""
    print(f"  {icon} {label}{detail_str}")


def cmd_status(args: argparse.Namespace) -> int:
    """Show current credential configuration status."""
    print_header("Credential Configuration Status")
    
    cred_path = get_credential_store_path()
    print(f"Credential Store: {cred_path}")
    print(f"Store Exists: {cred_path.exists()}")
    print()
    
    cred_manager = EnvCredentialManager("cli")
    print(f"Environment: {cred_manager.get_environment()}")
    print()
    
    print("Required Credentials:")
    required_creds = [
        "GITHUB_APP_ID",
        "GITHUB_APP_PRIVATE_KEY",
        "GITHUB_APP_INSTALLATION_ID"
    ]
    
    all_present = True
    for cred in required_creds:
        value = cred_manager.get_credential(cred)
        if value:
            masked = value[:4] + "..." if len(value) > 4 else "***"
            print_status(cred, True, f"configured ({masked})")
        else:
            print_status(cred, False, "not configured")
            all_present = False
    
    print()
    print("Optional Credentials:")
    optional_creds = [
        "GITHUB_APP_PRIVATE_KEY_PATH",
        "GITHUB_TOKEN"
    ]
    
    for cred in optional_creds:
        value = cred_manager.get_credential(cred)
        if value:
            masked = value[:4] + "..." if len(value) > 4 else "***"
            print_status(cred, True, f"configured ({masked})")
        else:
            print(f"  [--] {cred} - not configured (optional)")
    
    print()
    print("Dependencies:")
    print_status("PyJWT", HAS_JWT, "required for GitHub App auth")
    print_status("requests", HAS_REQUESTS, "required for API calls")
    
    print()
    return 0 if all_present else 1


def cmd_verify(args: argparse.Namespace) -> int:
    """Verify GitHub App authentication is working."""
    print_header("GitHub App Authentication Verification")
    
    agent_name = args.agent or "verification_test"
    print(f"Agent Name: {agent_name}")
    print()
    
    auth = get_github_app_auth(agent_name)
    result = auth.verify_installation()
    
    print("Configuration:")
    print_status("App Configured", result["configured"])
    print(f"  App ID: {result['app_id'] or 'not set'}")
    print(f"  Installation ID: {result['installation_id'] or 'not set'}")
    print(f"  Environment: {result['environment']}")
    print()
    
    print("Authentication:")
    print_status("JWT Generation", result["jwt_available"])
    print_status("Token Retrieval", result["token_available"])
    
    if result["error"]:
        print(f"\nError: {result['error']}")
    
    print()
    
    if result["token_available"]:
        print("GitHub App authentication is working correctly!")
        return 0
    elif result["jwt_available"]:
        print("JWT generation works, but token retrieval failed.")
        print("Check that the installation ID is correct and the app is installed.")
        return 1
    elif result["configured"]:
        print("Credentials are configured but JWT generation failed.")
        print("Check that the private key is valid.")
        return 1
    else:
        print("GitHub App is not fully configured.")
        print("Run 'python -m integration_validation.credential.cli setup' for help.")
        return 1


def cmd_test_github(args: argparse.Namespace) -> int:
    """Test GitHub API access with current credentials."""
    print_header("GitHub API Access Test")
    
    if not HAS_REQUESTS:
        print("Error: requests library not installed")
        print("Install with: pip install requests")
        return 1
    
    import requests
    
    agent_name = args.agent or "api_test"
    auth = get_github_app_auth(agent_name)
    headers = auth.get_auth_headers()
    
    if not headers:
        print("Error: Could not obtain authentication headers")
        print("Run 'python -m integration_validation.credential.cli verify' to diagnose")
        return 1
    
    print("Testing API access...")
    print()
    
    try:
        response = requests.get(
            "https://api.github.com/user",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print_status("API Access", True)
            print(f"  Authenticated as: {data.get('login', 'unknown')}")
            print(f"  Type: {data.get('type', 'unknown')}")
        elif response.status_code == 401:
            print_status("API Access", False, "authentication failed")
            return 1
        else:
            print_status("API Access", False, f"HTTP {response.status_code}")
            return 1
        
        response = requests.get(
            "https://api.github.com/installation/repositories",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            repos = data.get("repositories", [])
            print_status("Repository Access", True, f"{len(repos)} repositories")
            if repos and args.verbose:
                print("  Accessible repositories:")
                for repo in repos[:10]:
                    print(f"    - {repo['full_name']}")
                if len(repos) > 10:
                    print(f"    ... and {len(repos) - 10} more")
        else:
            print_status("Repository Access", False, f"HTTP {response.status_code}")
        
        print()
        print("GitHub API access is working!")
        return 0
        
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return 1


def cmd_setup(args: argparse.Namespace) -> int:
    """Interactive setup guide for GitHub App credentials."""
    print_header("GitHub App Setup Guide")
    
    print("This guide will help you set up GitHub App authentication for LOOVE AI agents.")
    print()
    
    print("Step 1: Create a GitHub App")
    print("-" * 40)
    print("1. Go to your GitHub organization settings")
    print("2. Navigate to: Developer settings > GitHub Apps > New GitHub App")
    print("3. Configure the app with these settings:")
    print("   - Name: LOOVE AI Agent Access (or similar)")
    print("   - Homepage URL: Your organization's URL")
    print("   - Webhook: Uncheck 'Active' (not needed)")
    print("   - Permissions:")
    print("     - Repository: Actions (Read/Write), Contents (Read/Write), Metadata (Read)")
    print("     - Organization: Members (Read) - optional")
    print("4. Click 'Create GitHub App'")
    print()
    
    print("Step 2: Generate a Private Key")
    print("-" * 40)
    print("1. On the app's settings page, scroll to 'Private keys'")
    print("2. Click 'Generate a private key'")
    print("3. Save the downloaded .pem file securely")
    print()
    
    print("Step 3: Install the App")
    print("-" * 40)
    print("1. On the app's settings page, click 'Install App'")
    print("2. Select your organization")
    print("3. Choose which repositories the app can access")
    print("4. Click 'Install'")
    print("5. Note the Installation ID from the URL:")
    print("   https://github.com/settings/installations/[INSTALLATION_ID]")
    print()
    
    print("Step 4: Configure Credentials")
    print("-" * 40)
    cred_path = get_credential_store_path()
    print(f"Add the following to: {cred_path}")
    print()
    print("```")
    print("GITHUB_APP_ID=your_app_id")
    print("GITHUB_APP_PRIVATE_KEY_PATH=/path/to/private-key.pem")
    print("GITHUB_APP_INSTALLATION_ID=your_installation_id")
    print("```")
    print()
    
    print("Or set as environment variables for CI/CD:")
    print("```")
    print("export GITHUB_APP_ID=your_app_id")
    print("export GITHUB_APP_PRIVATE_KEY='-----BEGIN RSA PRIVATE KEY-----\\n...'")
    print("export GITHUB_APP_INSTALLATION_ID=your_installation_id")
    print("```")
    print()
    
    print("Step 5: Verify Setup")
    print("-" * 40)
    print("Run: python -m integration_validation.credential.cli verify")
    print()
    
    if args.interactive:
        print("Interactive Configuration")
        print("-" * 40)
        
        app_id = input("Enter GitHub App ID (or press Enter to skip): ").strip()
        key_path = input("Enter path to private key .pem file (or press Enter to skip): ").strip()
        installation_id = input("Enter Installation ID (or press Enter to skip): ").strip()
        
        if app_id or key_path or installation_id:
            cred_path.parent.mkdir(parents=True, exist_ok=True)
            
            existing_content = ""
            if cred_path.exists():
                existing_content = cred_path.read_text()
            
            new_lines = []
            if app_id:
                new_lines.append(f"GITHUB_APP_ID={app_id}")
            if key_path:
                new_lines.append(f"GITHUB_APP_PRIVATE_KEY_PATH={key_path}")
            if installation_id:
                new_lines.append(f"GITHUB_APP_INSTALLATION_ID={installation_id}")
            
            if new_lines:
                with open(cred_path, "a") as f:
                    if existing_content and not existing_content.endswith("\n"):
                        f.write("\n")
                    f.write("\n".join(new_lines) + "\n")
                print(f"\nCredentials saved to {cred_path}")
                print("Run 'python -m integration_validation.credential.cli verify' to test.")
    
    return 0


def cmd_token(args: argparse.Namespace) -> int:
    """Generate and display an installation token."""
    agent_name = args.agent or "token_generator"
    auth = get_github_app_auth(agent_name)
    
    if args.quiet:
        token = auth.get_installation_token(force_refresh=args.refresh)
        if token:
            print(token)
            return 0
        return 1
    
    print_header("GitHub App Installation Token")
    
    if not auth.is_configured():
        print("Error: GitHub App is not configured")
        print("Run 'python -m integration_validation.credential setup' for help")
        return 1
    
    print(f"Agent: {agent_name}")
    print(f"App ID: {auth._app_id}")
    print(f"Installation ID: {auth._installation_id}")
    print()
    
    if args.refresh:
        print("Forcing token refresh...")
        auth._cached_token = None
        auth._token_expires_at = 0
    
    token = auth.get_installation_token()
    
    if not token:
        print("Error: Failed to generate installation token")
        print("Run 'python -m integration_validation.credential verify' to diagnose")
        return 1
    
    import time
    from datetime import datetime, timezone
    
    expires_at = auth._token_expires_at
    expires_dt = datetime.fromtimestamp(expires_at, tz=timezone.utc)
    time_remaining = expires_at - time.time()
    minutes_remaining = int(time_remaining / 60)
    
    print("Token Generated Successfully!")
    print("-" * 40)
    
    if args.show_token:
        print(f"Token: {token}")
    else:
        print(f"Token: {token[:20]}...{token[-10:]} (use --show-token to display full token)")
    
    print()
    print(f"Expires At: {expires_dt.isoformat()}")
    print(f"Time Remaining: {minutes_remaining} minutes")
    print()
    
    if args.export:
        import json
        token_data = {
            "token": token,
            "expires_at": expires_dt.isoformat(),
            "expires_timestamp": expires_at,
            "agent_name": agent_name,
            "app_id": auth._app_id,
            "installation_id": auth._installation_id
        }
        with open(args.export, "w") as f:
            json.dump(token_data, f, indent=2)
        print(f"Token data exported to: {args.export}")
    
    print("Note: Installation tokens expire after 1 hour.")
    print("The system automatically refreshes tokens 5 minutes before expiry.")
    
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    """Export current configuration as JSON."""
    print_header("Configuration Export")
    
    agent_name = args.agent or "export"
    auth = get_github_app_auth(agent_name)
    
    config = {
        "credential_store_path": str(get_credential_store_path()),
        "environment": auth._cred_manager.get_environment(),
        "github_app": {
            "configured": auth.is_configured(),
            "app_id": auth._app_id,
            "installation_id": auth._installation_id,
            "has_private_key": auth._private_key is not None
        },
        "dependencies": {
            "pyjwt": HAS_JWT,
            "requests": HAS_REQUESTS
        }
    }
    
    if args.output:
        with open(args.output, "w") as f:
            json.dump(config, f, indent=2)
        print(f"Configuration exported to: {args.output}")
    else:
        print(json.dumps(config, indent=2))
    
    return 0


def main() -> int:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Credential Management CLI for LOOVE AI Agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s status              Show current credential configuration
  %(prog)s setup               Display setup guide
  %(prog)s setup --interactive Interactive credential configuration
  %(prog)s verify              Verify GitHub App authentication
  %(prog)s test-github         Test GitHub API access
  %(prog)s token               Generate an installation token
  %(prog)s token --quiet       Output only the token (for scripting)
  %(prog)s token --refresh     Force token refresh
  %(prog)s export              Export configuration as JSON
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    status_parser = subparsers.add_parser("status", help="Show credential configuration status")
    
    setup_parser = subparsers.add_parser("setup", help="Setup guide for GitHub App credentials")
    setup_parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Enable interactive credential configuration"
    )
    
    verify_parser = subparsers.add_parser("verify", help="Verify GitHub App authentication")
    verify_parser.add_argument(
        "--agent", "-a",
        help="Agent name for verification (default: verification_test)"
    )
    
    test_parser = subparsers.add_parser("test-github", help="Test GitHub API access")
    test_parser.add_argument(
        "--agent", "-a",
        help="Agent name for testing (default: api_test)"
    )
    test_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed output"
    )
    
    export_parser = subparsers.add_parser("export", help="Export configuration as JSON")
    export_parser.add_argument(
        "--agent", "-a",
        help="Agent name for export"
    )
    export_parser.add_argument(
        "--output", "-o",
        help="Output file path (default: stdout)"
    )
    
    token_parser = subparsers.add_parser("token", help="Generate an installation token")
    token_parser.add_argument(
        "--agent", "-a",
        help="Agent name for token generation (default: token_generator)"
    )
    token_parser.add_argument(
        "--refresh", "-r",
        action="store_true",
        help="Force token refresh even if cached token is valid"
    )
    token_parser.add_argument(
        "--show-token", "-s",
        action="store_true",
        help="Display the full token (default: truncated for security)"
    )
    token_parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Output only the token (for scripting)"
    )
    token_parser.add_argument(
        "--export", "-e",
        help="Export token data to JSON file"
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    commands = {
        "status": cmd_status,
        "setup": cmd_setup,
        "verify": cmd_verify,
        "test-github": cmd_test_github,
        "export": cmd_export,
        "token": cmd_token
    }
    
    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
