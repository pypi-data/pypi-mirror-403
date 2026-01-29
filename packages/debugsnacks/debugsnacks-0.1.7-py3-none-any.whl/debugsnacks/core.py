import random
from .excuses import excuse
from .facts import fact

_CONFIG = {
    "verbosity": "fun",
    "chaos": 0
}

def config(**kwargs):
    _CONFIG.update(kwargs)

def auto():
    print("🎲 Toybox warming up...\n")
    random.choice([
        excuse,
        fact
    ])()

def exit(style="dramatic"):
    messages = {
        "dramatic": "And so, the program ends… not with a bang, but with a sigh.",
        "theatrical": "🎭 Exiting stage left. Applause optional.",
        "quiet": "Program terminated."
    }
    print(messages.get(style, messages["dramatic"]))
