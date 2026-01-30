import random

FACTS = [
    "🐙 Octopuses have three hearts.",
    "🧠 The human brain uses about 20% of the body’s energy.",
    "🐱 Cats sleep for around 70% of their lives.",
    "💻 The first computer bug was an actual moth.",
    "🕒 Programmers are most productive late at night."
]

def fact():
    print("📌 Fun fact:", random.choice(FACTS))
