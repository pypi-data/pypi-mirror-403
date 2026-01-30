import random
from .strings import DAD_JOKES

def say(text, mood="sarcastic"):
    comments = {
        "sarcastic": f"Oh wow. {text}. Truly groundbreaking.",
        "proud": f"✨ {text}. Look at you go!",
        "dramatic": f"{text.upper()}!!! THE DRAMA!",
        "casual": text
    }
    print(comments.get(mood, text))

def dadjoke():
    print(random.choice(DAD_JOKES))
