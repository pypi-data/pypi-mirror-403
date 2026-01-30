from datetime import datetime

def react():
    hour = datetime.now().hour
    if hour < 6:
        print("It’s way too late. Go to sleep, human.")
    elif hour < 12:
        print("Good morning. Coffee first. Code later.")
    elif hour < 18:
        print("Afternoon grind. Stay strong.")
    else:
        print("Evening coding session activated.")
