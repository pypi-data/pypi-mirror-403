import time
import debugsnacks

"""
Manual smoke tests for debugsnacks.

How to run:
    pip install -e .
    python tests/test_basic.py

Notes:
- These tests are for visual verification only.
- Outputs are intentionally random.
- No assertions are used by design.
"""

SEPARATOR = "-" * 50


def test_core_auto():
    print(f"\n{SEPARATOR}")
    print("=== Testing core.auto() ===")
    for i in range(5):
        print(f"\nRun #{i + 1}")
        debugsnacks.auto()
        time.sleep(0.2)


def test_core_exit():
    print(f"\n{SEPARATOR}")
    print("=== Testing core.exit() ===")
    styles = ["dramatic", "theatrical", "quiet", "unknown", None]

    for style in styles:
        print(f"\nExit style: {style}")
        try:
            debugsnacks.exit(style)
        except Exception as e:
            print("❌ Exception:", e)
        time.sleep(0.1)


def test_config():
    print(f"\n{SEPARATOR}")
    print("=== Testing core.config() ===")

    print("Default config behavior:")
    debugsnacks.auto()

    print("\nUpdating config values:")
    debugsnacks.config(verbosity="extra", chaos=2)
    debugsnacks.auto()

    print("\nResetting config:")
    debugsnacks.config(verbosity="fun", chaos=0)
    debugsnacks.auto()


def test_chaos():
    print(f"\n{SEPARATOR}")
    print("=== Testing chaos() ===")

    for level in [0, 1, 2, 3, -1, 99]:
        print(f"\nChaos level: {level}")
        try:
            debugsnacks.chaos(level)
        except Exception as e:
            print("❌ Exception:", e)
        time.sleep(0.1)


def test_excuses():
    print(f"\n{SEPARATOR}")
    print("=== Testing excuses.excuse() ===")

    for i in range(5):
        debugsnacks.excuse()
        time.sleep(0.1)


def test_facts():
    print(f"\n{SEPARATOR}")
    print("=== Testing facts.fact() ===")

    for i in range(5):
        debugsnacks.fact()
        time.sleep(0.1)


def test_humor_say():
    print(f"\n{SEPARATOR}")
    print("=== Testing humor.say() ===")

    moods = ["sarcastic", "proud", "dramatic", "casual", "unknown", None]

    for mood in moods:
        print(f"\nMood: {mood}")
        try:
            debugsnacks.say("You wrote a test", mood)
        except Exception as e:
            print("❌ Exception:", e)
        time.sleep(0.1)


def test_humor_dadjoke():
    print(f"\n{SEPARATOR}")
    print("=== Testing humor.dadjoke() ===")

    for i in range(5):
        debugsnacks.dadjoke()
        time.sleep(0.1)


def test_mood_react():
    print(f"\n{SEPARATOR}")
    print("=== Testing mood.react() ===")

    # Call multiple times to ensure stability
    for i in range(3):
        debugsnacks.react()
        time.sleep(0.3)


def run_all_tests():
    print("\n🚀 Starting debugsnacks smoke tests")

    test_core_auto()
    test_core_exit()
    test_config()
    test_chaos()
    test_excuses()
    test_facts()
    test_humor_say()
    test_humor_dadjoke()
    test_mood_react()

    print(f"\n{SEPARATOR}")
    print("✅ All tests executed successfully!")


if __name__ == "__main__":
    run_all_tests()
