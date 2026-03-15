#!/usr/bin/env python3
"""Print HERMES NEUROVISION in block-letter ASCII art with purple ANSI colors.
Run: python3 print_banner.py
Screenshot the output on a black terminal background.
"""

# Purple gradient — top line brightest, bottom darkest
G = [
    "\033[1;38;5;201m",   # bright magenta-purple  (row 0)
    "\033[1;38;5;171m",   # vivid purple           (row 1)
    "\033[38;5;135m",     # mid purple             (row 2)
    "\033[38;5;99m",      # deeper purple          (row 3)
    "\033[38;5;63m",      # dark purple            (row 4)
    "\033[38;5;57m",      # deep violet            (row 5)
]
DIM   = "\033[38;5;241m"  # dim grey — shadow/connector chars
PINK  = "\033[1;38;5;213m"
RESET = "\033[0m"

# Each row: apply gradient color, dim colour for ░ ╗ ╔ ╚ ╝ chars
def R(line, color):
    out = color
    for ch in line:
        if ch in "░╗╔╚╝╩╦╠╣╬":
            out += DIM + ch + color
        else:
            out += ch
    return out + RESET

HERMES = [
    " ██╗  ██╗███████╗██████╗ ███╗   ███╗███████╗███████╗",
    " ██║  ██║██╔════╝██╔══██╗████╗ ████║██╔════╝██╔════╝",
    " ███████║█████╗  ██████╔╝██╔████╔██║█████╗  ███████╗",
    " ██╔══██║██╔══╝  ██╔══██╗██║╚██╔╝██║██╔══╝  ╚════██║",
    " ██║  ██║███████╗██║  ██║██║ ╚═╝ ██║███████╗███████║",
    " ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝╚══════╝",
]

NEUROVISION = [
    " ███╗   ██╗███████╗██╗   ██╗██████╗  ██████╗ ██╗   ██╗██╗███████╗██╗ ██████╗ ███╗   ██╗",
    " ████╗  ██║██╔════╝██║   ██║██╔══██╗██╔═══██╗██║   ██║██║██╔════╝██║██╔═══██╗████╗  ██║",
    " ██╔██╗ ██║█████╗  ██║   ██║██████╔╝██║   ██║██║   ██║██║███████╗██║██║   ██║██╔██╗ ██║",
    " ██║╚██╗██║██╔══╝  ██║   ██║██╔══██╗██║   ██║╚██╗ ██╔╝██║╚════██║██║██║   ██║██║╚██╗██║",
    " ██║ ╚████║███████╗╚██████╔╝██║  ██║╚██████╔╝ ╚████╔╝ ██║███████║██║╚██████╔╝██║ ╚████║",
    " ╚═╝  ╚═══╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝ ╚═════╝   ╚═══╝  ╚═╝╚══════╝╚═╝ ╚═════╝ ╚═╝  ╚═══╝",
]

print()
print()

for i, line in enumerate(HERMES):
    print(R(line, G[i]))

print()

for i, line in enumerate(NEUROVISION):
    print(R(line, G[min(i + 1, 5)]))

print()
print()
print(f"  {PINK}github.com/Tranquil-Flow/hermes-neurovision{RESET}")
print()
print(f"  \033[2;37mBuild your own screen today!{RESET}")
print(f"  \033[38;5;241mThen ask your agent to generate a screen based on your idea!{RESET}")
print()
print()
