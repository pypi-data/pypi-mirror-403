class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def print_colored(text, color, **kwargs):
    print(f"{color}{text}{Colors.END}", **kwargs)

def print_banner():
    banner = f"""
{Colors.CYAN}{Colors.BOLD}
╔════════════════════════════════════════════════════════════╗
║                   QwenVPFCode-AI v1.0.0                    ║
║  Fast Local AI Assistant - No Filters - Complete Memory    ║
╚════════════════════════════════════════════════════════════╝
{Colors.YELLOW}
Made by litaliano00-dev (https://github.com/litaliano00-dev)
Organization: OPFTS
Model: Qwen2.5-Coder-1.5B-Instruct
{Colors.END}
"""
    print(banner)

def print_help():
    help_text = f"""
{Colors.GREEN}{Colors.BOLD}Commands:{Colors.END}
{Colors.YELLOW}/clear{Colors.END} - Clear conversation memory
{Colors.YELLOW}/save{Colors.END} - Save conversation to file
{Colors.YELLOW}/load{Colors.END} - Load conversation from file
{Colors.YELLOW}/exit{Colors.END} - Exit the program
{Colors.YELLOW}/help{Colors.END} - Show this help
"""
    print(help_text)

def stream_response(text, color=Colors.CYAN, delay=0.01):
    """
    Stream text character by character for a more interactive feel.
    """
    for char in text:
        print(f"{color}{char}{Colors.END}", end='', flush=True)
        time.sleep(delay)
    print()  # Newline at end
