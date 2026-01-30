import random

def say(text, mood="sarcastic"):
    comments = {
        "sarcastic": f"Oh wow. {text}. Truly groundbreaking.",
        "proud": f"✨ {text}. Look at you go!",
        "dramatic": f"{text.upper()}!!! THE DRAMA!",
        "casual": text
    }
    print(comments.get(mood, text))

def dadjoke():
    jokes = [
        "Why do programmers prefer dark mode? Because light attracts bugs.",
        "I would tell you a UDP joke, but you might not get it.",
        "Why did the developer go broke? Because he used up all his cache."
    ]
    print(random.choice(jokes))
