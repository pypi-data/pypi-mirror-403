"""Interactive CLI for COBOL MCP Server setup."""
import os
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


def _read_key():
    """Read a single keypress (Unix). Returns key string."""
    import select
    import tty
    import termios
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = os.read(fd, 1)
        if ch == b'\x1b':
            if select.select([fd], [], [], 0.3)[0]:
                ch2 = os.read(fd, 1)
                if ch2 == b'[' and select.select([fd], [], [], 0.3)[0]:
                    ch3 = os.read(fd, 1)
                    if ch3 == b'A':
                        return 'up'
                    if ch3 == b'B':
                        return 'down'
            return 'esc'
        if ch in (b'\r', b'\n'):
            return 'enter'
        if ch == b' ':
            return 'space'
        if ch in (b'a', b'A'):
            return 'a'
        if ch in (b'q', b'Q'):
            return 'q'
        if ch == b'\x03':
            raise KeyboardInterrupt
        return ch.decode('utf-8', errors='replace')
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def _interactive_select(ides: list[str]) -> list[str]:
    """Arrow-key multi-select for TTY environments."""
    cursor = 0
    checked = [False] * len(ides)
    total_items = len(ides) + 1  # IDEs + Proceed
    num_lines = total_items + 2  # items + blank + hint line

    def render():
        sys.stdout.write(f"\033[{num_lines}A")
        for i, ide in enumerate(ides):
            arrow = f"{CYAN}\u276f{NC}" if i == cursor else " "
            mark = f"{GREEN}x{NC}" if checked[i] else " "
            sys.stdout.write(f"\033[2K  {arrow} [{mark}] {ide}\n")
        # Proceed option
        arrow = f"{CYAN}\u276f{NC}" if cursor == len(ides) else " "
        has_selection = any(checked)
        proceed_label = f"{GREEN}Proceed{NC}" if has_selection else f"{RED}Proceed{NC} (select at least one)"
        sys.stdout.write(f"\033[2K  {arrow} {proceed_label}\n")
        sys.stdout.write(f"\033[2K\n")
        sys.stdout.write(f"\033[2K  {CYAN}\u2191/\u2193{NC} navigate  {CYAN}\u23ce{NC} select  {CYAN}a{NC} all\n")
        sys.stdout.flush()

    # Initial draw
    sys.stdout.write("\n" * num_lines)
    render()

    while True:
        key = _read_key()
        if key == 'up':
            cursor = (cursor - 1) % total_items
        elif key == 'down':
            cursor = (cursor + 1) % total_items
        elif key in ('enter', 'space'):
            if cursor < len(ides):
                checked[cursor] = not checked[cursor]
            else:
                # Proceed
                selected = [ide for ide, c in zip(ides, checked) if c]
                if not selected:
                    render()
                    continue
                sys.stdout.write(f"\033[{num_lines}A")
                for _ in range(num_lines):
                    sys.stdout.write("\033[2K\n")
                sys.stdout.write(f"\033[{num_lines}A")
                sys.stdout.flush()
                return selected
        elif key == 'a':
            toggle = not all(checked)
            checked = [toggle] * len(ides)
        elif key in ('q', 'esc'):
            sys.stdout.write(f"\033[{num_lines}A")
            for _ in range(num_lines):
                sys.stdout.write("\033[2K\n")
            sys.stdout.write(f"\033[{num_lines}A")
            sys.stdout.flush()
            print("Setup cancelled.")
            sys.exit(0)
        render()


def _fallback_select(ides: list[str]) -> list[str]:
    """Number-based fallback for non-TTY environments."""
    for i, ide in enumerate(ides, 1):
        print(f"  {CYAN}{i:2}.{NC} {ide}")
    print(f"\n  {CYAN} a.{NC} All IDEs")
    print(f"  {CYAN} q.{NC} Quit\n")

    selection = input("Enter numbers separated by spaces (e.g., 1 3 5) or 'a' for all: ").strip().lower()

    if selection == 'q':
        print("Setup cancelled.")
        sys.exit(0)
    if selection == 'a':
        return ides.copy()

    selected = []
    for part in selection.split():
        try:
            idx = int(part) - 1
            if 0 <= idx < len(ides):
                selected.append(ides[idx])
        except ValueError:
            continue

    if not selected:
        print(f"{RED}\u2717 No valid IDEs selected{NC}")
        sys.exit(1)
    return selected


def select_ides() -> list[str]:
    print(f"{BLUE}\u2501" * 53 + f"{NC}")
    print(f"{BOLD}Step 2: Select IDEs to configure{NC}")
    print(f"{BLUE}\u2501" * 53 + f"{NC}\n")

    use_interactive = (
        sys.stdin.isatty()
        and sys.stdout.isatty()
        and os.name != 'nt'
    )

    if use_interactive:
        try:
            selected = _interactive_select(SUPPORTED_IDES)
        except (ImportError, OSError):
            selected = _fallback_select(SUPPORTED_IDES)
    else:
        selected = _fallback_select(SUPPORTED_IDES)

    print(f"{GREEN}\u2713 Selected: {', '.join(selected)}{NC}\n")
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
