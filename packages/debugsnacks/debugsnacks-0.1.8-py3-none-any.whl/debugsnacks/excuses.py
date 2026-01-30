import random

EXCUSES = [
    "It works on my machine.",
    "Quantum fluctuations broke the code.",
    "The bug ran away when I opened the debugger.",
    "Cosmic rays flipped a bit.",
    "I blame the compiler."
]

def excuse():
    print(random.choice(EXCUSES))
