# Load valid words from text file
import os
words_file = os.path.join(os.path.dirname(__file__), "data", "valid_words.txt")
with open(words_file, "r") as f:
    VALID_WORDS = set(word.strip().upper() for word in f if word.strip())

# Check if a word is valid for Wordle gameplay.
def is_valid_word(word: str) -> bool:
    return word.upper() in VALID_WORDS

# Evaluate a guess against the target word.
def evaluate_guess(target: str, guess: str):
    target = target.upper()
    guess = guess.upper()
    result = ["miss"] * len(target)

# First pass: mark correct positions and count remaining letters
    target_counts = {}
    for i, (s, g) in enumerate(zip(target, guess)):
        if g == s:
            result[i] = "correct"
        else:
            target_counts[s] = target_counts.get(s, 0) + 1

# Second pass: mark letters that are present but in wrong position
    for i, (s, g) in enumerate(zip(target, guess)):
        if result[i] == "correct":
            continue
        if target_counts.get(g, 0) > 0:
            result[i] = "present"
            target_counts[g] -= 1

    return result
