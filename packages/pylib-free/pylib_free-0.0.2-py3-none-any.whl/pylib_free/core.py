# ----- core.py ----- #
import time
import os
import random
import math
import sys
import json
import re
import datetime
from collections import Counter, defaultdict, deque
from itertools import permutations, combinations, product, cycle

# ----- Time / Sleep -----
def wait(seconds):
    time.sleep(seconds)

def localtime():
    return time.strftime("%Y-%m-%d %H:%M:%S")

def timestamp():
    return int(time.time())

def sleep_until(target_time):
    """Pause bis zu einem bestimmten Unix-Timestamp"""
    now = time.time()
    if target_time > now:
        time.sleep(target_time - now)

def stopwatch(func, *args, **kwargs):
    """Misst die Ausführungszeit einer Funktion"""
    start = time.time()
    result = func(*args, **kwargs)
    end = time.time()
    print(f"Execution time: {end - start:.4f}s")
    return result

# ----- System / OS -----
def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def listdir(path="."):
    return os.listdir(path)

def file_exists(path):
    return os.path.exists(path)

def make_dir(path):
    os.makedirs(path, exist_ok=True)

def exit_program():
    sys.exit()

def current_path():
    return os.getcwd()

# ----- Random / Math -----
def randnum(num1, num2):
    return random.randint(num1, num2)

def randfloat(a, b):
    return random.uniform(a, b)

def choice(seq):
    return random.choice(seq)

def shuffle_list(lst):
    random.shuffle(lst)
    return lst

def coinflip():
    return random.choice([True, False])

def sqrt(x):
    return math.sqrt(x)

def factorial(x):
    return math.factorial(x)

def ceil(x):
    return math.ceil(x)

def floor(x):
    return math.floor(x)

# ----- Strings -----
def uppercase(s):
    return s.upper()

def lowercase(s):
    return s.lower()

def strip(s):
    return s.strip()

def replace(s, old, new):
    return s.replace(old, new)

def split(s, sep=None):
    return s.split(sep)

def join(sep, iterable):
    return sep.join(iterable)

def is_number(s):
    try:
        float(s)
        return True
    except:
        return False

# ----- Lists / Iterables -----
def first(lst):
    return lst[0] if lst else None

def last(lst):
    return lst[-1] if lst else None

def list_len(lst):
    return len(lst)

def flatten(lst_of_lsts):
    return [item for sublist in lst_of_lsts for item in sublist]

def unique(lst):
    return list(set(lst))

def count_elements(lst):
    return Counter(lst)

# ----- Dictionaries -----
def dict_keys(d):
    return list(d.keys())

def dict_values(d):
    return list(d.values())

def dict_items(d):
    return list(d.items())

def get_safe(d, key, default=None):
    return d.get(key, default)

def merge_dicts(d1, d2):
    return {**d1, **d2}

# ----- JSON -----
def json_load(path):
    with open(path, "r") as f:
        return json.load(f)

def json_dump(obj, path):
    with open(path, "w") as f:
        json.dump(obj, f, indent=4)

def json_loads(s):
    return json.loads(s)

def json_dumps(obj):
    return json.dumps(obj)

# ----- Regex -----
def regex_match(pattern, string):
    return re.match(pattern, string)

def regex_search(pattern, string):
    return re.search(pattern, string)

def regex_findall(pattern, string):
    return re.findall(pattern, string)

def regex_sub(pattern, repl, string):
    return re.sub(pattern, repl, string)

# ----- Itertools -----
def permute(iterable, r=None):
    return list(permutations(iterable, r))

def combine(iterable, r):
    return list(combinations(iterable, r))

def cross_product(*iterables):
    return list(product(*iterables))

def endless_cycle(iterable):
    return cycle(iterable)

# ----- Datetime -----
def now():
    return datetime.datetime.now()

def today():
    return datetime.date.today()

def add_days(date_obj, days):
    return date_obj + datetime.timedelta(days=days)
