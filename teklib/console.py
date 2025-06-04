import sys
import os

# Detect if ANSI is supported (Windows 10 1607+)
def supports_ansi():
    if os.name != "nt":
        return True
    ver = sys.getwindowsversion()
    return ver.major > 10 or (ver.major == 10 and ver.build >= 14393)

# Enable ANSI escape codes if supported
USE_ANSI = supports_ansi()

# ANSI color codes (disabled if unsupported)
RED = "\033[91m" if USE_ANSI else ""
YELLOW = "\033[93m" if USE_ANSI else ""
CYAN = "\033[96m" if USE_ANSI else ""
GREEN = "\033[92m" if USE_ANSI else ""
RESET = "\033[0m" if USE_ANSI else ""

def success(msg):
    print(f"{GREEN}[OK]{RESET}     {msg}")

def error(msg):
    print(f"{RED}[FAIL]{RESET}   {msg}", file=sys.stderr)
    # sys.exit(1)

def warning(msg):
    print(f"{YELLOW}[WARN]{RESET}   {msg}", file=sys.stderr)

def notice(msg):
    print(f"{CYAN}[INFO]{RESET}   {msg}")

def checksum_message(text, calculated, expected = None, fail = 2):
    if (expected == None):
        notice(f"{text:<35} = {calculated:08X}")
    elif (calculated == expected):
        success(f"{text:<35} = {calculated:08X} --> {GREEN}OK{RESET}")
    else:
        if fail == 2:
          error(f"{text:<35} = {calculated:08X} --> {RED}BAD{RESET}: expected {expected:08X}")
        elif fail == 1:
          warning(f"{text:<35} = {calculated:08X} --> {RED}BAD{RESET}: expected {expected:08X}")
        else:
          notice(f"{text:<35} = {calculated:08X} --> {RED}BAD{RESET}: expected {expected:08X}")