"""
CLI interface for COBOL MCP Server setup.
"""
import sys
import argparse
from .setup import setup_mcp_config, SUPPORTED_IDES


def print_banner():
    """Print the COBOL MCP banner."""
    print("""
 ██████╗ ██████╗ ██████╗  ██████╗ ██╗         ███╗   ███╗ ██████╗██████╗ 
██╔════╝██╔═══██╗██╔══██╗██╔═══██╗██║         ████╗ ████║██╔════╝██╔══██╗
██║     ██║   ██║██████╔╝██║   ██║██║         ██╔████╔██║██║     ██████╔╝
██║     ██║   ██║██╔══██╗██║   ██║██║         ██║╚██╔╝██║██║     ██╔═══╝ 
╚██████╗╚██████╔╝██████╔╝╚██████╔╝███████╗    ██║ ╚═╝ ██║╚██████╗██║     
 ╚═════╝ ╚═════╝ ╚═════╝  ╚═════╝ ╚══════╝    ╚═╝     ╚═╝ ╚═════╝╚═╝     
    """)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="COBOL MCP Server - Static analysis and documentation search for COBOL",
        prog="cobol-mcp"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Setup command
    setup_parser = subparsers.add_parser(
        "setup",
        help="Set up COBOL MCP Server for your IDE"
    )
    setup_parser.add_argument(
        "api_key",
        help="Your COBOL MCP API key"
    )
    setup_parser.add_argument(
        "--ide",
        choices=SUPPORTED_IDES,
        default="cursor",
        help=f"IDE to configure (default: cursor). Options: {', '.join(SUPPORTED_IDES)}"
    )

    # List IDEs command
    subparsers.add_parser(
        "list-ides",
        help="List all supported IDEs"
    )

    args = parser.parse_args()

    if args.command == "setup":
        print_banner()

        if not args.api_key or len(args.api_key) < 8:
            print("❌ Invalid API key. Please provide a valid API key.")
            sys.exit(1)

        success = setup_mcp_config(args.api_key, args.ide)
        sys.exit(0 if success else 1)

    elif args.command == "list-ides":
        print("\n🖥️  Supported IDEs:\n")
        for ide in sorted(SUPPORTED_IDES):
            print(f"  • {ide}")
        print(f"\n💡 Usage: cobol-mcp setup YOUR_API_KEY --ide {SUPPORTED_IDES[0]}\n")
        sys.exit(0)

    # No command - show help
    parser.print_help()
    sys.exit(1)


if __name__ == "__main__":
    main()
