import debugsnacks
import time

def test_core():
    print("\n=== Testing core.auto() ===")
    for _ in range(3):  # call multiple times to see random outputs
        debugsnacks.auto()
        time.sleep(0.3)

    print("\n=== Testing core.exit() ===")
    for style in ["dramatic", "theatrical", "quiet", "unknown"]:
        debugsnacks.exit(style)
        time.sleep(0.1)

def test_chaos():
    print("\n=== Testing chaos() ===")
    for level in range(3):
        debugsnacks.chaos(level)
        time.sleep(0.1)

def test_excuses():
    print("\n=== Testing excuses.excuse() ===")
    for _ in range(3):
        debugsnacks.excuse()
        time.sleep(0.1)

def test_facts():
    print("\n=== Testing facts.fact() ===")
    for _ in range(3):
        debugsnacks.fact()
        time.sleep(0.1)

def test_humor():
    print("\n=== Testing humor.say() ===")
    moods = ["sarcastic", "proud", "dramatic", "casual", "unknown"]
    for mood in moods:
        debugsnacks.say("You wrote a test!", mood)
        time.sleep(0.1)

    print("\n=== Testing humor.dadjoke() ===")
    for _ in range(3):
        debugsnacks.dadjoke()
        time.sleep(0.1)

def test_mood():
    print("\n=== Testing mood.react() ===")
    debugsnacks.react()

def run_all_tests():
    test_core()
    test_chaos()
    test_excuses()
    test_facts()
    test_humor()
    test_mood()
    print("\n✅ All tests executed!")

if __name__ == "__main__":
    run_all_tests()
