import random
from .strings import CHAOS_MESSAGES

def chaos(level=1):
    messages = CHAOS_MESSAGES.get(level, CHAOS_MESSAGES[2])
    print(random.choice(messages))
