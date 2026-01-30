"""Docker-style name generator for chat threads.

Generates memorable names like 'happy_panda' or 'clever_fox'.
"""

import random

# Adjectives - positive, memorable, easy to type
ADJECTIVES = [
    "bold",
    "brave",
    "bright",
    "calm",
    "clever",
    "cool",
    "eager",
    "fair",
    "fast",
    "fierce",
    "gentle",
    "happy",
    "keen",
    "kind",
    "lively",
    "lucky",
    "merry",
    "mighty",
    "noble",
    "proud",
    "quick",
    "quiet",
    "sharp",
    "shy",
    "sleek",
    "smart",
    "smooth",
    "snappy",
    "speedy",
    "steady",
    "swift",
    "tender",
    "vivid",
    "warm",
    "wise",
    "witty",
    "zen",
]

# Nouns - animals and nature, easy to remember
NOUNS = [
    "badger",
    "bear",
    "bird",
    "bison",
    "cat",
    "crane",
    "crow",
    "deer",
    "dolphin",
    "dove",
    "eagle",
    "elk",
    "falcon",
    "finch",
    "fox",
    "frog",
    "gull",
    "hare",
    "hawk",
    "heron",
    "horse",
    "jay",
    "lark",
    "lion",
    "lynx",
    "moose",
    "otter",
    "owl",
    "panda",
    "pike",
    "puma",
    "raven",
    "robin",
    "salmon",
    "seal",
    "shark",
    "snake",
    "sparrow",
    "squid",
    "stork",
    "swan",
    "tiger",
    "trout",
    "turtle",
    "whale",
    "wolf",
    "wren",
]


def generate_thread_name() -> str:
    """Generate a random Docker-style name.

    Returns:
        A name in the format 'adjective_noun' like 'happy_panda'.
    """
    adjective = random.choice(ADJECTIVES)
    noun = random.choice(NOUNS)
    return f"{adjective}_{noun}"


def generate_unique_thread_name(existing_names: set[str]) -> str:
    """Generate a unique thread name that doesn't conflict with existing names.

    Args:
        existing_names: Set of names already in use.

    Returns:
        A unique name. If collision occurs, appends a number.
    """
    base_name = generate_thread_name()

    if base_name not in existing_names:
        return base_name

    # If collision, try with numbers
    for i in range(2, 100):
        numbered_name = f"{base_name}_{i}"
        if numbered_name not in existing_names:
            return numbered_name

    # Fallback: regenerate with different words
    for _ in range(10):
        new_name = generate_thread_name()
        if new_name not in existing_names:
            return new_name

    # Ultimate fallback: add random suffix
    return f"{base_name}_{random.randint(100, 999)}"
