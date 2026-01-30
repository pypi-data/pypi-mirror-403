import time
import sys
from functools import wraps

REGISTRY = {"sec": 1, "min": 60, "hr": 3600}

def parse_time(user_input):
    user_input = user_input.lower().strip()
    for unit, multiplier in REGISTRY.items():
        if unit in user_input:
            try:
                num = float(user_input.replace(unit, "").strip())
                return int(num * multiplier)
            except ValueError: continue
    try: return int(user_input)
    except ValueError: return None

def countdown(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        while True:
            val = input("\n--- Banana Timer ---\nEnter duration: ")
            seconds = parse_time(val)
            if seconds is None: continue
            for i in range(seconds, 0, -1):
                sys.stdout.write(f"\rTime remaining: {i//60:02d}:{i%60:02d}")
                sys.stdout.flush()
                time.sleep(1)
            print("\nTime's up!")
            result = func(*args, **kwargs)
            if input("\n'c' to continue: ").lower() != 'c': break
        return result
    return wrapper
