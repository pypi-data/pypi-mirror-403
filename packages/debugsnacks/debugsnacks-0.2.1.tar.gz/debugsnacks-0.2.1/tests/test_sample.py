import time
import random

import debugsnacks as ds


def process_file(filename):
    """Pretend to process a file"""
    ds.say(f"Processing {filename}", mood="casual")
    time.sleep(1)

    # Random failure
    if random.random() < 0.3:
        raise RuntimeError("Processing failed")

    ds.say(f"{filename} processed successfully", mood="proud")


def main():
    # Startup
    ds.auto()
    ds.react()

    files = ["report.csv", "data.json", "image.png", "backup.zip"]

    ds.say("Starting daily batch job", mood="dramatic")
    time.sleep(1)

    for file in files:
        try:
            process_file(file)
        except Exception as e:
            ds.say(str(e), mood="sarcastic")
            ds.excuse()

            # Escalate chaos after failure
            ds.chaos(level=2)
            time.sleep(1)

    # Add some fun at the end
    ds.fact()
    ds.dadjoke()

    # Exit like a professional™
    ds.exit(style="theatrical")


if __name__ == "__main__":
    main()
