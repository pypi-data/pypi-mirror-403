import random
from .excuses import excuse
from .facts import fact
from .strings import EXIT_MESSAGES

_CONFIG = {
    "verbosity": "fun",
    "chaos": 0
}

def config(**kwargs):
    _CONFIG.update(kwargs)

def auto():
    print("🎲 Toybox warming up...\n")
    random.choice([excuse, fact])()

def exit(style="dramatic"):
    messages = EXIT_MESSAGES.get(style, EXIT_MESSAGES["dramatic"])
    print(random.choice(messages))
