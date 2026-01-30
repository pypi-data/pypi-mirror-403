from datetime import datetime
import random
from .strings import REACT_MESSAGES

def react():
    hour = datetime.now().hour

    if hour < 6:
        print(random.choice(REACT_MESSAGES["late_night"]))
    elif hour < 12:
        print(random.choice(REACT_MESSAGES["morning"]))
    elif hour < 18:
        print(random.choice(REACT_MESSAGES["afternoon"]))
    else:
        print(random.choice(REACT_MESSAGES["evening"]))
