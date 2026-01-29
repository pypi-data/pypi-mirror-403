"""Interactive CLI for COBOL MCP Server setup."""
import sys
from .setup import setup_mcp_config, SUPPORTED_IDES

BLUE = '\033[0;34m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
CYAN = '\033[0;36m'
RED = '\033[0;31m'
BOLD = '\033[1m'
NC = '\033[0m'


def print_banner():
    print(f"""{CYAN}
 ██████╗ ██████╗ ██████╗  ██████╗ ██╗         ███╗   ███╗ ██████╗██████╗ 
██╔════╝██╔═══██╗██╔══██╗██╔═══██╗██║         ████╗ ████║██╔════╝██╔══██╗
██║     ██║   ██║██████╔╝██║   ██║██║         ██╔████╔██║██║     ██████╔╝
██║     ██║   ██║██╔══██╗██║   ██║██║         ██║╚██╔╝██║██║     ██╔═══╝ 
╚██████╗╚██████╔╝██████╔╝╚██████╔╝███████╗    ██║ ╚═╝ ██║╚██████╗██║     
 ╚═════╝ ╚═════╝ ╚═════╝  ╚═════╝ ╚══════╝    ╚═╝     ╚═╝ ╚═════╝╚═╝     
{NC}""")
    print(f"  {BOLD}COBOL Static Analysis & Documentation Search{NC}\n")


def get_api_key() -> str:
    print(f"{BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{NC}")
    print(f"{BOLD}Step 1: API Key{NC}")
    print(f"{BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{NC}\n")
    
    api_key = input(f"Enter your API key: ").strip()
    
    if not api_key or len(api_key) < 8:
        print(f"\n{RED}✗ Invalid API key{NC}")
        sys.exit(1)
    
    print(f"{GREEN}✓ API key accepted{NC}\n")
    return api_key


def select_ides() -> list[str]:
    print(f"{BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{NC}")
    print(f"{BOLD}Step 2: Select IDEs to configure{NC}")
    print(f"{BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{NC}\n")
    
    for i, ide in enumerate(SUPPORTED_IDES, 1):
        print(f"  {CYAN}{i:2}.{NC} {ide}")
    
    print(f"\n  {CYAN} a.{NC} All IDEs")
    print(f"  {CYAN} q.{NC} Quit\n")
    
    selection = input(f"Enter numbers separated by spaces (e.g., 1 3 5) or 'a' for all: ").strip().lower()
    
    if selection == 'q':
        print("Setup cancelled.")
        sys.exit(0)
    
    if selection == 'a':
        return SUPPORTED_IDES.copy()
    
    selected = []
    for part in selection.split():
        try:
            idx = int(part) - 1
            if 0 <= idx < len(SUPPORTED_IDES):
                selected.append(SUPPORTED_IDES[idx])
        except ValueError:
            continue
    
    if not selected:
        print(f"{RED}✗ No valid IDEs selected{NC}")
        sys.exit(1)
    
    print(f"\n{GREEN}✓ Selected: {', '.join(selected)}{NC}\n")
    return selected


def run_setup(api_key: str, ides: list[str]):
    print(f"{BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{NC}")
    print(f"{BOLD}Step 3: Configuring IDEs{NC}")
    print(f"{BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{NC}\n")
    
    success_count = 0
    for ide in ides:
        print(f"  Configuring {ide}...", end=" ", flush=True)
        if setup_mcp_config(api_key, ide, quiet=True):
            print(f"{GREEN}✓{NC}")
            success_count += 1
        else:
            print(f"{RED}✗{NC}")
    
    print(f"\n{BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{NC}")
    print(f"{BOLD}Setup Complete!{NC}")
    print(f"{BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{NC}\n")
    
    print(f"  {GREEN}✓{NC} {success_count}/{len(ides)} IDEs configured successfully\n")
    print(f"  {YELLOW}→{NC} Restart your IDE(s) to use COBOL MCP\n")
    print(f"  Available tools:")
    print(f"    • check(file_path) - Analyze COBOL source for issues")
    print(f"    • search(query) - Search COBOL documentation")
    print(f"    • translate_reference(topic) - COBOL-to-Java patterns\n")


def interactive_setup():
    print_banner()
    api_key = get_api_key()
    ides = select_ides()
    run_setup(api_key, ides)


def main():
    if len(sys.argv) < 2:
        print("Usage: cobol-mcp setup [API_KEY] [--ide IDE]")
        print("       cobol-mcp list-ides")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "list-ides":
        print("\nSupported IDEs:\n")
        for ide in sorted(SUPPORTED_IDES):
            print(f"  • {ide}")
        print(f"\nUsage: cobol-mcp setup YOUR_API_KEY --ide {SUPPORTED_IDES[0]}\n")
        sys.exit(0)
    
    if command == "setup":
        # Parse arguments
        api_key = None
        ide = None
        
        args = sys.argv[2:]
        i = 0
        while i < len(args):
            if args[i] == "--ide" and i + 1 < len(args):
                ide = args[i + 1]
                i += 2
            elif args[i] in ["--help", "-h"]:
                print("Usage: cobol-mcp setup [API_KEY] [--ide IDE]")
                sys.exit(0)
            elif not args[i].startswith("-") and api_key is None:
                api_key = args[i]
                i += 1
            else:
                i += 1
        
        print_banner()
        
        # Get API key if not provided
        if not api_key:
            api_key = get_api_key()
        else:
            if len(api_key) < 8:
                print(f"{RED}✗ Invalid API key{NC}")
                sys.exit(1)
            print(f"{GREEN}✓ API key accepted{NC}\n")
        
        # Get IDE(s) - prompt if not specified with --ide
        if ide:
            if ide not in SUPPORTED_IDES:
                print(f"{RED}✗ Unknown IDE: {ide}{NC}")
                print(f"Supported: {', '.join(SUPPORTED_IDES)}")
                sys.exit(1)
            ides = [ide]
        else:
            ides = select_ides()
        
        run_setup(api_key, ides)
        sys.exit(0)
    
    if command in ["--help", "-h"]:
        print("Usage: cobol-mcp setup [API_KEY] [--ide IDE]")
        print("       cobol-mcp list-ides")
        sys.exit(0)
    
    print(f"Unknown command: {command}")
    sys.exit(1)


if __name__ == "__main__":
    main()
